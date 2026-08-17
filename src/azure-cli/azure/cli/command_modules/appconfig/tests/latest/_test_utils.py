# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os

from azure.cli.testsdk.scenario_tests import RecordingProcessor
from azure.cli.testsdk.scenario_tests.utilities import is_json_payload
from azure.cli.testsdk.exceptions import CliTestError
from azure.cli.core.util import shell_safe_json_parse

def create_config_store(test, kwargs, disable_local_auth=False):
    if 'retention_days' not in kwargs:
        kwargs.update({
            'retention_days': 1
        })
    command = 'appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --retention-days {retention_days}'
    if disable_local_auth:
        command += ' --disable-local-auth true'
    test.cmd(command)


def _get_local_test_resource_prefix():
    return os.environ.get("AZURE_CLI_LOCAL_TEST_RESOURCE_PREFIX")

def get_resource_name_prefix(prefix):
    resource_prefix = _get_local_test_resource_prefix()
    return prefix if resource_prefix is None else resource_prefix + prefix

# Value the reused live test resource group (AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME) is rewritten to
# in recordings by ResourceGroupNameReplacer, and returned by get_test_resource_group() during
# playback so requests match the sanitized cassettes. Matches the default ResourceGroupPreparer() moniker.
SANITIZED_TEST_RESOURCE_GROUP = "clitest.rg000001"

def get_test_resource_group():
    resource_group = os.environ.get("AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME")
    if resource_group:
        return resource_group
    # The stub only exists inside sanitized recordings; a live run needs a real group where the
    # recording principal holds "App Configuration Data Owner".
    if os.environ.get("AZURE_TEST_RUN_LIVE"):
        raise CliTestError(
            "Set AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME to a resource group where you hold "
            "'App Configuration Data Owner' to record App Configuration data-plane tests.")
    return SANITIZED_TEST_RESOURCE_GROUP


def _case_insensitive_query_matcher(r1, r2):
    """ Ensure method, path, and query parameters match.

    Query parameter names are case-insensitive (e.g. OData '$select' vs '$Select'),
    so normalize the keys before comparing to avoid spurious cassette mismatches
    caused by SDK serialization differences across versions.
    """
    from urllib.parse import urlparse, parse_qs

    url1 = urlparse(r1.uri)
    url2 = urlparse(r2.uri)

    q1 = {k.lower(): v for k, v in parse_qs(url1.query).items()}
    q2 = {k.lower(): v for k, v in parse_qs(url2.query).items()}
    shared_keys = set(q1.keys()).intersection(set(q2.keys()))

    if len(shared_keys) != len(q1) or len(shared_keys) != len(q2):
        return False

    for key in shared_keys:
        if q1[key][0].lower() != q2[key][0].lower():
            return False

    return True


def register_appconfig_query_matcher(test):
    """ Register the App Configuration case-insensitive query matcher on the test's VCR instance. """
    test.vcr.register_matcher('query', _case_insensitive_query_matcher)


class OperationLocationSanitizer(RecordingProcessor):
    """ Scrub the store name from the 'operation-location' response header.

    App Configuration snapshot long-running operations return the store endpoint in the
    'operation-location' header, which the SDK follows to poll for completion. The base
    GeneralNameReplacer only sanitizes the 'location' and 'azure-asyncoperation' headers,
    so without this the real store name leaks into recordings and breaks playback (the
    poller targets the un-sanitized host).
    """

    def __init__(self, name_replacer):
        self._name_replacer = name_replacer

    def process_response(self, response):
        for old, new in self._name_replacer.names_name:
            self._name_replacer.replace_header(response, 'operation-location', old, new)
        return response


class ResourceGroupNameReplacer(RecordingProcessor):
    """ Scrub the reused live test resource group name from recordings.

    Data-plane tests reuse a pre-provisioned resource group (AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME)
    that holds a standing "App Configuration Data Owner" role. That name is never registered with the
    base name-replacer, so rewrite it to the value get_test_resource_group() returns during playback.
    """

    def __init__(self):
        self._real_rg = os.environ.get("AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME")

    def _scrub(self, value):
        if self._real_rg and value:
            return value.replace(self._real_rg, SANITIZED_TEST_RESOURCE_GROUP)
        return value

    def process_request(self, request):
        request.uri = self._scrub(request.uri)
        if isinstance(request.body, bytes):
            try:
                request.body = self._scrub(request.body.decode('utf-8')).encode('utf-8')
            except UnicodeDecodeError:
                pass
        elif request.body:
            request.body = self._scrub(request.body)
        return request

    def process_response(self, response):
        if response.get('body', {}).get('string'):
            response['body']['string'] = self._scrub(response['body']['string'])
        return response


def register_appconfig_recording_processors(test):
    """ Register App Configuration-specific recording processors on the test. """
    test.recording_processors.append(OperationLocationSanitizer(test.name_replacer))
    test.recording_processors.append(ResourceGroupNameReplacer())

class CredentialResponseSanitizer(RecordingProcessor):
    def process_response(self, response):
        if is_json_payload(response):
            try:
                json_data = shell_safe_json_parse(response["body"]["string"])

                if isinstance(json_data.get("value"), list):
                    for idx, credential in enumerate(json_data["value"]):
                        self._try_replace_secret(credential, idx)

                    response["body"]["string"] = json.dumps(json_data)
                
                elif isinstance(json_data, dict):
                    self._try_replace_secret(json_data)

                    response["body"]["string"] = json.dumps(json_data)

            except Exception:
                pass

        return response

    def _try_replace_secret(self, credential, idx = 0):
        if "connectionString" in credential:
            credential["id"] = "sanitized_id{}".format(idx + 1)
            credential["value"] = "sanitized_secret{}".format(idx + 1)

            endpoint = next(
                filter(lambda x: x.startswith("Endpoint="), credential["connectionString"].split(";")))[len("Endpoint="):]

            credential["connectionString"] = "Endpoint={};Id={};Secret={}".format(
                endpoint, credential["id"], credential["value"])
