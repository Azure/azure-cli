# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os

from azure.cli.testsdk.scenario_tests import RecordingProcessor
from azure.cli.testsdk.scenario_tests.utilities import is_json_payload
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

def get_test_resource_group():
    # Data-plane tests use Microsoft Entra ID (--auth-mode login) against a store whose local auth
    # is disabled. The recording principal must already hold "App Configuration Data Owner" at a
    # scope covering the store, so tests target a fixed resource group with that standing role
    # instead of an ephemeral @ResourceGroupPreparer group. Override via AZURE_CLI_APPCONFIG_TEST_RG.
    return os.environ.get("AZURE_CLI_APPCONFIG_TEST_RG", "mametcal-python")


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


def register_appconfig_recording_processors(test):
    """ Register App Configuration-specific recording processors on the test. """
    test.recording_processors.append(OperationLocationSanitizer(test.name_replacer))

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
