# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

from azure.appconfiguration import ConfigurationSetting
from azure.cli.core import get_default_cli
from azure.cli.core.azclierror import InvalidArgumentValueError, FileOperationError
from azure.cli.command_modules.appconfig import keyvalue, _kv_export_helpers, _utils
from azure.cli.command_modules.appconfig._constants import ImportExportProfiles


class ImportProfileDetectionTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = os.path.join(self.directory.name, "kvset.json")
        self.data = {"profile": ImportExportProfiles.KVSET, "items": []}

    def write_file(self):
        with open(self.path, "w", encoding="utf-8") as target:
            json.dump(self.data, target)

    def test_kvset_export_embeds_profile(self):
        export = getattr(_kv_export_helpers, "__export_kvset_to_file")
        export(self.path, [ConfigurationSetting(key="Example", value="value")], yes=True)
        with open(self.path, encoding="utf-8") as source:
            data = json.load(source)
        self.assertEqual(ImportExportProfiles.KVSET, data["profile"])
        self.assertEqual("Example", data["items"][0]["key"])
        self.assertEqual("value", data["items"][0]["value"])

    def test_kv_import_detects_profile_in_handler_and_cli(self):
        self.write_file()
        with patch.object(keyvalue, "get_appconfig_data_client", return_value=Mock()), \
                patch.object(keyvalue, "__import_kvset_from_file") as importer:
            keyvalue.import_config(None, "file", path=self.path, format_="json", yes=True)
            importer.assert_called_once()
            importer.reset_mock()
            result = get_default_cli().invoke([
                "appconfig", "kv", "import", "--name", "Destination", "--source", "file",
                "--format", "json", "--path", self.path, "--yes",
            ])
            self.assertEqual(0, result)
            importer.assert_called_once()

    def test_kvset_json_fixture_autodetects_profile(self):
        path = os.path.join(os.path.dirname(__file__), "kvset_no_features.json")
        with open(path, encoding="utf-8") as source:
            data = json.load(source)
        self.assertEqual(ImportExportProfiles.KVSET, data["profile"])
        self.assertTrue(data["items"])
        with patch.object(keyvalue, "get_appconfig_data_client", return_value=Mock()), \
                patch.object(keyvalue, "__import_kvset_from_file") as importer:
            result = get_default_cli().invoke([
                "appconfig", "kv", "import", "--name", "Destination", "--source", "file",
                "--format", "json", "--path", path, "--yes",
            ])
            self.assertEqual(0, result)
            importer.assert_called_once()
            self.assertEqual(path, importer.call_args.kwargs["path"])

    def test_detected_kvset_enforces_argument_restrictions_before_connecting(self):
        self.write_file()
        for arguments in ({"label": "test"}, {"prefix": "prefix"}, {"separator": "."},
                          {"depth": 2}, {"tags": {"team": "app"}}, {"skip_features": True},
                          {"content_type": "application/json"}):
            with self.subTest(arguments=arguments), \
                    patch.object(keyvalue, "get_appconfig_data_client") as client:
                with self.assertRaises(InvalidArgumentValueError):
                    keyvalue.import_config(None, "file", path=self.path, format_="json", **arguments)
                client.assert_not_called()

    def test_invalid_embedded_profile_is_rejected(self):
        self.data["profile"] = ImportExportProfiles.FFSET
        self.write_file()
        with patch.object(keyvalue, "get_appconfig_data_client") as client:
            with self.assertRaises(InvalidArgumentValueError):
                keyvalue.import_config(None, "file", path=self.path, format_="json")
            client.assert_not_called()

    def test_kv_import_preserves_application_profile_key(self):
        for profile in ("production", ImportExportProfiles.KVSET):
            with self.subTest(profile=profile):
                self.data = {"profile": profile, "Example": "value"}
                self.write_file()
                with patch.object(keyvalue, "get_appconfig_data_client", return_value=Mock()), \
                        patch.object(keyvalue, "__read_kv_from_config_store", return_value=[]), \
                        patch.object(keyvalue, "__write_kv_and_features_to_config_store") as writer:
                    result = get_default_cli().invoke([
                        "appconfig", "kv", "import", "--name", "Destination", "--source", "file",
                        "--format", "json", "--path", self.path, "--yes",
                    ])
                    self.assertEqual(0, result)
                    imported = writer.call_args.kwargs["key_values"]
                    self.assertEqual(self.data, {item.key: item.value for item in imported})

    def test_profile_detection_requires_known_profile_and_items_array(self):
        supported = (ImportExportProfiles.DEFAULT, ImportExportProfiles.KVSET)
        for profile in ("production", "appconfig/unknown", None, 1, {}):
            with self.subTest(profile=profile):
                self.assertEqual(ImportExportProfiles.DEFAULT, _utils.resolve_import_profile(
                    {"profile": profile, "items": []}, None, supported))
        for items in (None, {}, "value"):
            with self.subTest(items=items):
                self.assertEqual(ImportExportProfiles.DEFAULT, _utils.resolve_import_profile(
                    {"profile": ImportExportProfiles.KVSET, "items": items}, None, supported))

    def test_explicit_kvset_overrides_metadata_and_supports_older_files(self):
        for data in ({"profile": "unknown", "items": []}, {"items": []}):
            self.data = data
            self.write_file()
            with patch.object(keyvalue, "get_appconfig_data_client", return_value=Mock()), \
                    patch.object(keyvalue, "__import_kvset_from_file") as importer:
                keyvalue.import_config(None, "file", path=self.path, format_="json",
                                       profile=ImportExportProfiles.KVSET, yes=True)
                importer.assert_called_once()

    def test_explicit_default_and_unmarked_files_keep_default_behavior(self):
        for profile, data in ((None, {"Example": "value"}),
                              (ImportExportProfiles.DEFAULT, self.data)):
            self.data = data
            self.write_file()
            with patch.object(keyvalue, "get_appconfig_data_client", return_value=Mock()), \
                    patch.object(keyvalue, "__read_kv_from_file", side_effect=RuntimeError("default reader")), \
                    patch.object(keyvalue, "__import_kvset_from_file") as importer:
                with self.assertRaisesRegex(RuntimeError, "default reader"):
                    keyvalue.import_config(None, "file", path=self.path, format_="json", profile=profile)
                importer.assert_not_called()

    def test_malformed_file_reports_error_before_connecting(self):
        with open(self.path, "w", encoding="utf-8") as target:
            target.write("{")
        with patch.object(keyvalue, "get_appconfig_data_client") as client:
            with self.assertRaisesRegex(FileOperationError, "The input is not a well formatted json file"):
                keyvalue.import_config(None, "file", path=self.path, format_="json")
            client.assert_not_called()

    def test_profile_detection_preserves_default_scalar_json_error(self):
        for value in ("invalid plain string", None, True, 42):
            with self.subTest(value=value):
                self.data = value
                self.write_file()
                errors = []
                for profile in (None, ImportExportProfiles.DEFAULT):
                    with patch.object(keyvalue, "get_appconfig_data_client", return_value=Mock()):
                        with self.assertRaises(FileOperationError) as result:
                            keyvalue.import_config(None, "file", path=self.path, format_="json", profile=profile)
                        errors.append(str(result.exception))
                self.assertEqual(errors[0], errors[1])
                self.assertEqual(
                    "The input is not a well formatted json file.\nException: "
                    "Json object required but type '{}' was given.".format(type(value).__name__),
                    errors[0])

    def test_profile_detection_preserves_missing_file_error(self):
        with patch.object(keyvalue, "get_appconfig_data_client") as client:
            with self.assertRaisesRegex(FileOperationError, "^File is not available\\.$"):
                keyvalue.import_config(None, "file", path=self.path, format_="json")
            client.assert_not_called()
