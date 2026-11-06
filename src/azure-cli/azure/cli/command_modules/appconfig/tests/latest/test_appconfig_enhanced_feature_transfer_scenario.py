# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import time
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import yaml
from azure.core.exceptions import HttpResponseError
from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

from azure.cli.command_modules.appconfig.enhanced_feature_import_export import _get_client
from azure.cli.command_modules.appconfig.tests.latest._test_utils import (
    AppConfigResourceGroupPreparer,
    CredentialResponseSanitizer,
    create_config_store,
    register_appconfig_query_matcher,
    register_appconfig_recording_processors,
)

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class AppConfigEnhancedFeatureTransferScenarioTest(ScenarioTest):
    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)
        register_appconfig_query_matcher(self)
        register_appconfig_recording_processors(self)
        self.vcr.register_matcher("feature_transfer_request", self._request_matcher)
        self.vcr.match_on = (*self.vcr.match_on, "feature_transfer_request")

    @staticmethod
    def _request_matcher(recorded, actual):
        if recorded.path.startswith("/ff/") and actual.path.startswith("/ff/"):
            for header in ("If-Match", "If-None-Match"):
                assert recorded.headers.get(header) == actual.headers.get(header), \
                    "{} differs from the recorded request".format(header)
            if recorded.method == actual.method == "PUT":
                assert json.loads(recorded.body) == json.loads(actual.body), \
                    "Feature flag request body differs from the recording"

    def _wait_for_data_access(self, endpoint):
        client = _get_client(SimpleNamespace(cli_ctx=self.cli_ctx), None, None, "login", endpoint)
        with client:
            for attempt in range(31):
                try:
                    list(client.list_feature_flags(name_filter="*", label_filter="\0"))
                    return
                except HttpResponseError as exception:
                    if exception.status_code not in (401, 403) or attempt == 30:
                        raise
                    if self.in_recording:
                        time.sleep(10)

    def _create_store(self, prefix, resource_group, location):
        name = self.create_random_name(prefix=prefix, length=24)
        self.kwargs.update(config_store_name=name, rg=resource_group, rg_loc=location, sku="standard")
        create_config_store(self, self.kwargs, disable_local_auth=True)
        self.addCleanup(self._delete_store, name)
        endpoint = "https://{}.azconfig.io".format(name)
        self._wait_for_data_access(endpoint)
        return endpoint

    def _delete_store(self, name):
        self.kwargs["cleanup_store"] = name
        self.cmd("appconfig delete --name {cleanup_store} --resource-group {rg} --yes")

    def _export(self, endpoint, path, format_="json", options=""):
        self.kwargs.update(transfer_endpoint=endpoint, transfer_path=path,
                           transfer_format=format_, transfer_options=options)
        self.cmd('appconfig enhanced-feature-flag export --endpoint {transfer_endpoint} --auth-mode login '
                 '--destination file --format {transfer_format} --path "{transfer_path}" --yes {transfer_options}')
        with open(path, encoding="utf-8") as source:
            return json.load(source) if format_ == "json" else yaml.safe_load(source)

    def _import(self, endpoint, path, format_="json", options=""):
        self.kwargs.update(transfer_endpoint=endpoint, transfer_path=path,
                           transfer_format=format_, transfer_options=options)
        self.cmd('appconfig enhanced-feature-flag import --endpoint {transfer_endpoint} --auth-mode login '
                 '--source file --format {transfer_format} --path "{transfer_path}" --yes {transfer_options}')

    @staticmethod
    def _sorted_flags(flags):
        return sorted(flags, key=lambda flag: (flag.get("name", flag.get("id")), flag.get("label") or ""))

    @AppConfigResourceGroupPreparer(parameter_name_for_location="location", location="eastus")
    @AllowLargeResponse()
    def test_azconfig_enhanced_feature_import_export_profiles(self, resource_group, location):
        source_endpoint = self._create_store("fftransfersrc", resource_group, location)
        destination_endpoint = self._create_store("fftransferdst", resource_group, location)
        fixture = os.path.join(TEST_DIR, "enhanced-feature-flags-test.json")
        with TemporaryDirectory(prefix="ff-transfer-", dir=TEST_DIR) as directory:
            default_json = os.path.join(directory, "default.json")
            default_yaml = os.path.join(directory, "default.yaml")
            ffset_json = os.path.join(directory, "ffset.json")
            ffset_yaml = os.path.join(directory, "ffset.yaml")
            destination_json = os.path.join(directory, "destination.json")

            self._import(source_endpoint, fixture, options="--profile appconfig/ffset")
            application = self._export(source_endpoint, default_json)
            self.assertEqual({"feature_management"}, set(application))
            flags = application["feature_management"]["feature_flags"]
            self.assertEqual(2, len(flags))
            self.assertTrue(all("id" in flag and not any(
                key in flag for key in ("name", "label", "tags", "etag", "last_modified")) for flag in flags))
            variant = next(flag for flag in flags if flag["id"] == "CliLiveTestVariant")
            self.assertEqual({"color": "blue"}, variant["variants"][0]["configuration_value"])

            self._import(destination_endpoint, default_json)
            round_trip = self._export(destination_endpoint, destination_json)
            self.assertEqual(self._sorted_flags(flags),
                             self._sorted_flags(round_trip["feature_management"]["feature_flags"]))
            explicit_default = self._export(source_endpoint, default_yaml, "yaml",
                                            "--profile appconfig/default")
            self.assertEqual(application, explicit_default)
            self._import(destination_endpoint, default_yaml, "yaml",
                         "--profile appconfig/default --strict")
            self.assertEqual(application, self._export(destination_endpoint, destination_json))

            self._import(source_endpoint, fixture, options="--profile appconfig/ffset --preserve-labels")
            resource_set = self._export(source_endpoint, ffset_json,
                                        options='--profile appconfig/ffset --label "*"')
            self.assertEqual("appconfig/ffset", resource_set["profile"])
            self.assertEqual(4, len(resource_set["items"]))
            self.assertEqual({None, "cli-ff-import-export-test"},
                             {flag.get("label") for flag in resource_set["items"]})
            self.assertTrue(all("name" in flag and not any(
                key in flag for key in ("id", "etag", "last_modified")) for flag in resource_set["items"]))
            self._import(destination_endpoint, ffset_json, options="--preserve-labels --strict")
            imported = self._export(destination_endpoint, destination_json,
                                    options='--profile appconfig/ffset --label "*"')
            self.assertEqual(self._sorted_flags(resource_set["items"]),
                             self._sorted_flags(imported["items"]))

            yaml_set = self._export(source_endpoint, ffset_yaml, "yaml",
                                    '--profile appconfig/ffset --label "*"')
            self.assertEqual(resource_set, yaml_set)
            self._import(destination_endpoint, ffset_yaml, "yaml", "--preserve-labels")
            after_yaml = self._export(destination_endpoint, destination_json,
                                      options='--profile appconfig/ffset --label "*"')
            self.assertEqual(imported, after_yaml)

            with open(ffset_json, "w", encoding="utf-8") as target:
                json.dump(dict(resource_set, profile="appconfig/default"), target)
            self._import(destination_endpoint, ffset_json,
                         options="--profile appconfig/ffset --preserve-labels")
            after_override = self._export(destination_endpoint, destination_json,
                                          options='--profile appconfig/ffset --label "*"')
            self.assertEqual(imported, after_override)

            preview = os.path.join(directory, "preview.json")
            self.kwargs.update(source_endpoint=source_endpoint, destination_endpoint=destination_endpoint,
                               preview_path=preview, import_preview_path=ffset_yaml)
            self.cmd('appconfig enhanced-feature-flag export --endpoint {source_endpoint} --auth-mode login '
                     '--destination file --format json --path "{preview_path}" --feature-name CliLiveTest* '
                     '--tags purpose=cli-live-test --dry-run')
            self.assertFalse(os.path.exists(preview))
            self.cmd('appconfig enhanced-feature-flag import --endpoint {destination_endpoint} --auth-mode login '
                     '--source file --format yaml --path "{import_preview_path}" --preserve-labels --dry-run')
            self.cmd('appconfig enhanced-feature-flag export --endpoint {source_endpoint} --auth-mode login '
                     '--destination appconfig --dest-endpoint {destination_endpoint} --dest-auth-mode login '
                     '--label "*" --preserve-labels --yes')
            self.cmd('appconfig enhanced-feature-flag import --endpoint {destination_endpoint} --auth-mode login '
                     '--source appconfig --src-endpoint {source_endpoint} --src-auth-mode login '
                     '--src-feature-name CliLiveTest* --src-label cli-ff-import-export-test '
                     '--label store-copy --yes')
            self.cmd('appconfig enhanced-feature-flag list --endpoint {destination_endpoint} --auth-mode login '
                     '--label store-copy --all',
                     checks=[self.check("length(@)", 2)])
