# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
from contextlib import redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

import yaml
from azure.appconfiguration import FeatureFlag
from azure.core import MatchConditions
from azure.core.exceptions import HttpResponseError
from azure.cli.core.azclierror import (
    AzureResponseError,
    FileOperationError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    RequiredArgumentMissingError,
)

from azure.cli.command_modules.appconfig import enhanced_feature_import_export as transfers
from azure.cli.command_modules.appconfig import _utils
from azure.cli.command_modules.appconfig._constants import ImportExportProfiles


class EnhancedFeatureClientTests(TestCase):
    def test_key_auth_uses_resolved_connection_string(self):
        with patch.object(_utils, "FeatureFlagClient") as client_type, \
                patch.object(_utils, "resolve_connection_string", return_value="resolved") as resolve:
            result = _utils.get_appconfig_feature_flag_client(None, "Store", None, "key", None)
            resolve.assert_called_once_with(None, "Store", None)
            self.assertIs(client_type.from_connection_string.return_value, result)
            self.assertEqual("resolved", client_type.from_connection_string.call_args.kwargs["connection_string"])

    def test_login_auth_uses_shared_credential_for_both_resource_types(self):
        credential = Mock()
        endpoint = "https://example.azconfig.io"
        for helper, type_name in ((_utils.get_appconfig_feature_flag_client, "FeatureFlagClient"),
                                  (_utils.get_appconfig_data_client, "AzureAppConfigurationClient")):
            with self.subTest(type_name=type_name), \
                    patch.object(_utils, type_name) as client_type, \
                    patch.object(_utils, "resolve_login_credential", return_value=(credential, endpoint)):
                self.assertIs(client_type.return_value, helper(None, "Store", None, "login", None))
                self.assertIs(credential, client_type.call_args.kwargs["credential"])
                self.assertEqual(endpoint, client_type.call_args.kwargs["base_url"])

    def test_anonymous_auth_uses_header_stripping_transport(self):
        with patch.object(_utils, "FeatureFlagClient") as client_type:
            _utils.get_appconfig_feature_flag_client(None, None, None, "anonymous", "http://localhost:8483")
            self.assertIsInstance(client_type.call_args.kwargs["transport"], _utils.AuthHeaderRequestsTransport)
            self.assertEqual("http://localhost:8483", client_type.call_args.kwargs["base_url"])

    def test_both_clients_receive_retry_policy(self):
        policy = Mock()
        for helper, type_name in ((_utils.get_appconfig_feature_flag_client, "FeatureFlagClient"),
                                  (_utils.get_appconfig_data_client, "AzureAppConfigurationClient")):
            with self.subTest(type_name=type_name), \
                    patch.object(_utils, type_name) as client_type, \
                    patch.object(_utils, "_get_data_plane_retry_policy", return_value=policy):
                helper(None, None, None, "anonymous", "http://localhost:8483")
                self.assertIs(policy, client_type.call_args.kwargs["retry_policy"])


class EnhancedFeatureImportExportTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = os.path.join(self.directory.name, "flags.json")
        self.client = Mock()
        self.client.list_feature_flags.return_value = []
        self.get_client = patch.object(transfers, "_get_client", return_value=self.client).start()
        self.confirm = patch.object(transfers, "user_confirmation").start()
        self.addCleanup(patch.stopall)
        self.resource = {
            "name": "Beta",
            "enabled": False,
            "label": "test",
            "description": "Enhanced flag",
            "conditions": {"requirement_type": "All", "filters": [
                {"name": "TimeWindow", "parameters": {"Start": "2026-01-01T00:00:00Z"}}
            ]},
            "variants": [{"name": "Red", "value": '{"color":"red"}',
                          "content_type": "application/json", "status_override": "Enabled"}],
            "allocation": {"default_when_enabled": "Red", "default_when_disabled": "Red", "seed": "seed"},
            "telemetry": {"enabled": False, "metadata": {"team": "app"}},
            "tags": {"team": "app"},
        }
        self.application_resource = {
            "id": "Beta",
            "enabled": False,
            "description": "Enhanced flag",
            "conditions": {"requirement_type": "All", "client_filters": [
                {"name": "TimeWindow", "parameters": {"Start": "2026-01-01T00:00:00Z"}}
            ]},
            "variants": [{"name": "Red", "configuration_value": {"color": "red"},
                          "status_override": "Enabled"}],
            "allocation": self.resource["allocation"],
            "telemetry": self.resource["telemetry"],
        }

    def write_file(self, data, format_="json"):
        with open(self.path, "w", encoding="utf-8") as target:
            if format_ == "json":
                json.dump(data, target)
            else:
                yaml.safe_dump(data, target)

    def import_file(self, **kwargs):
        kwargs.setdefault("profile", ImportExportProfiles.FFSET)
        transfers.import_feature_flags(None, "file", path=self.path, format_="json", **kwargs)

    def test_file_round_trip_preserves_entire_enhanced_resource(self):
        for format_ in ("json", "yaml"):
            with self.subTest(format_=format_):
                flag = FeatureFlag.from_dict(self.resource)
                flag.etag = "source-etag"
                flag.last_modified = datetime(2026, 1, 1, tzinfo=timezone.utc)
                self.client.list_feature_flags.return_value = [flag]
                transfers.export_feature_flags(None, "file", path=self.path, format_=format_,
                                               profile=ImportExportProfiles.FFSET, yes=True)
                with open(self.path, encoding="utf-8") as source:
                    exported = json.load(source) if format_ == "json" else yaml.safe_load(source)
                self.assertEqual({"profile": ImportExportProfiles.FFSET, "items": [self.resource]}, exported)
                self.assertEqual("source-etag", flag.etag)
                self.assertEqual(datetime(2026, 1, 1, tzinfo=timezone.utc), flag.last_modified)
                self.client.list_feature_flags.return_value = []
                transfers.import_feature_flags(None, "file", path=self.path, format_=format_,
                                               profile=ImportExportProfiles.FFSET, preserve_labels=True, yes=True)
                written = self.client.set_feature_flag.call_args.args[0]
                self.assertEqual(self.resource, written.as_dict(keep_readonly=False))
                self.assertNotIn("id", written.as_dict())

    def test_import_command_parses_labels_tags_and_import_mode(self):
        from azure.cli.core import get_default_cli

        self.write_file([self.resource])
        result = get_default_cli().invoke([
            "appconfig", "enhanced-feature-flag", "import", "-n", "Destination",
            "-s", "file", "--path", self.path, "--format", "json", "--preserve-labels",
            "--profile", ImportExportProfiles.FFSET,
            "--tags", "new=value", "--import-mode", "all", "--yes",
        ])
        self.assertEqual(0, result)
        written = self.client.set_feature_flag.call_args.args[0]
        self.assertEqual("test", written.label)
        self.assertEqual({"new": "value"}, written.tags)

    def test_import_command_can_clear_source_tags(self):
        from azure.cli.core import get_default_cli

        self.write_file([self.resource])
        result = get_default_cli().invoke([
            "appconfig", "enhanced-feature-flag", "import", "-n", "Destination",
            "-s", "file", "--path", self.path, "--format", "json", "--tags", "", "--yes",
            "--profile", ImportExportProfiles.FFSET,
        ])
        self.assertEqual(0, result)
        self.assertEqual({}, self.client.set_feature_flag.call_args.args[0].tags)

    def test_export_command_parses_filters_and_destination_tags(self):
        from azure.cli.core import get_default_cli

        source_client = Mock()
        source_client.list_feature_flags.return_value = [FeatureFlag.from_dict(self.resource)]
        self.get_client.side_effect = [source_client, self.client]
        result = get_default_cli().invoke([
            "appconfig", "enhanced-feature-flag", "export", "-n", "Source",
            "-d", "appconfig", "--dest-name", "Destination", "--feature-name", "Beta*",
            "--label", "*", "--tags", "team=app", "--dest-tags", "new=value",
            "--dest-label", "production", "--yes",
        ])
        self.assertEqual(0, result)
        source_client.list_feature_flags.assert_called_once_with(
            name_filter="Beta*", label_filter="*", tags_filter=["team=app"])
        written = self.client.set_feature_flag.call_args.args[0]
        self.assertEqual("production", written.label)
        self.assertEqual({"new": "value"}, written.tags)

    def test_export_command_defaults_to_null_label(self):
        from azure.cli.core import get_default_cli

        flags = [FeatureFlag(name=name, enabled=True) for name in ("First", "Second", "Third")]
        self.client.list_feature_flags.side_effect = (
            lambda **kwargs: flags if kwargs["label_filter"] == "\0" else [])
        result = get_default_cli().invoke([
            "appconfig", "enhanced-feature-flag", "export", "-n", "Source",
            "-d", "file", "--path", self.path, "--format", "json", "--yes",
        ])
        self.assertEqual(0, result)
        self.client.list_feature_flags.assert_called_once_with(
            name_filter="*", label_filter="\0", tags_filter=None)
        with open(self.path, encoding="utf-8") as source:
            exported = json.load(source)
        self.assertEqual({"feature_management": {"feature_flags": [
            {"id": name, "enabled": True} for name in ("First", "Second", "Third")
        ]}}, exported)

    def test_default_profile_exports_application_schema_in_json_and_yaml(self):
        for format_ in ("json", "yaml"):
            with self.subTest(format_=format_):
                flag = FeatureFlag.from_dict(self.resource)
                flag.etag = "source-etag"
                flag.last_modified = datetime(2026, 1, 1, tzinfo=timezone.utc)
                self.client.list_feature_flags.return_value = [flag]
                transfers.export_feature_flags(None, "file", path=self.path, format_=format_, yes=True)
                with open(self.path, encoding="utf-8") as source:
                    data = json.load(source) if format_ == "json" else yaml.safe_load(source)
                self.assertEqual({"feature_management": {"feature_flags": [self.application_resource]}}, data)

    def test_default_profile_imports_application_schema_in_json_and_yaml(self):
        expected = dict(self.resource, label="production", tags={"new": "tag"})
        for format_ in ("json", "yaml"):
            with self.subTest(format_=format_):
                self.client.set_feature_flag.reset_mock()
                self.write_file({"feature_management": {"feature_flags": [self.application_resource]}}, format_)
                transfers.import_feature_flags(None, "file", path=self.path, format_=format_,
                                               label="production", tags={"new": "tag"}, yes=True)
                written = transfers._serialize_flag(self.client.set_feature_flag.call_args.args[0])
                # JSON whitespace is not semantically significant.
                self.assertEqual(json.loads(expected["variants"][0]["value"]),
                                 json.loads(written["variants"][0]["value"]))
                written["variants"][0]["value"] = expected["variants"][0]["value"]
                self.assertEqual(expected, written)

    def test_default_profile_import_command_parses_file_and_profile(self):
        from azure.cli.core import get_default_cli

        self.write_file({"feature_management": {"feature_flags": [{"id": "Beta", "enabled": True}]}})
        result = get_default_cli().invoke([
            "appconfig", "enhanced-feature-flag", "import", "-n", "Destination",
            "-s", "file", "--path", self.path, "--format", "json",
            "--profile", ImportExportProfiles.DEFAULT, "--yes",
        ])
        self.assertEqual(0, result)
        flag = self.client.set_feature_flag.call_args.args[0]
        self.assertEqual("Beta", flag.name)
        self.assertTrue(flag.enabled)
        self.assertIsNone(flag.label)

    def test_default_profile_import_defaults_missing_enabled_to_false(self):
        self.write_file({"feature_management": {"feature_flags": [{"id": "Beta"}]}})
        transfers.import_feature_flags(None, "file", path=self.path, format_="json", yes=True)
        flag = self.client.set_feature_flag.call_args.args[0]
        self.assertEqual("Beta", flag.name)
        self.assertFalse(flag.enabled)
        self.assertIsNotNone(flag.enabled)

    def test_ffset_profile_export_command_preserves_resource_schema(self):
        from azure.cli.core import get_default_cli

        self.client.list_feature_flags.return_value = [FeatureFlag.from_dict(self.resource)]
        result = get_default_cli().invoke([
            "appconfig", "enhanced-feature-flag", "export", "-n", "Source",
            "-d", "file", "--path", self.path, "--format", "json",
            "--profile", ImportExportProfiles.FFSET, "--label", "*", "--yes",
        ])
        self.assertEqual(0, result)
        with open(self.path, encoding="utf-8") as source:
            self.assertEqual({"profile": ImportExportProfiles.FFSET, "items": [self.resource]}, json.load(source))

    def test_ffset_export_autodetects_on_import_for_both_formats(self):
        from azure.cli.core import get_default_cli

        for format_ in ("json", "yaml"):
            with self.subTest(format_=format_):
                self.client.list_feature_flags.return_value = [FeatureFlag.from_dict(self.resource)]
                transfers.export_feature_flags(None, "file", path=self.path, format_=format_,
                                               profile=ImportExportProfiles.FFSET, yes=True)
                self.client.list_feature_flags.return_value = []
                self.client.set_feature_flag.reset_mock()
                result = get_default_cli().invoke([
                    "appconfig", "enhanced-feature-flag", "import", "-n", "Destination",
                    "-s", "file", "--path", self.path, "--format", format_,
                    "--preserve-labels", "--yes",
                ])
                self.assertEqual(0, result)
                self.assertEqual(self.resource, transfers._serialize_flag(
                    self.client.set_feature_flag.call_args.args[0]))

    def test_invalid_embedded_feature_profiles_fail_before_connecting(self):
        for profile in (None, 1, {}, "appconfig/kvset", "unknown"):
            with self.subTest(profile=profile):
                self.write_file({"profile": profile, "items": [self.resource]})
                with self.assertRaises(InvalidArgumentValueError):
                    transfers.import_feature_flags(None, "file", path=self.path, format_="json", yes=True)
                self.get_client.assert_not_called()

    def test_explicit_feature_profile_overrides_embedded_metadata(self):
        self.write_file({"profile": "unknown", "items": [self.resource]})
        self.import_file(preserve_labels=True, yes=True)
        self.assertEqual(self.resource, transfers._serialize_flag(
            self.client.set_feature_flag.call_args.args[0]))
        self.write_file({"profile": ImportExportProfiles.FFSET,
                         "feature_management": {"feature_flags": [{"id": "Beta", "enabled": False}]}})
        transfers.import_feature_flags(None, "file", path=self.path, format_="json",
                                       profile=ImportExportProfiles.DEFAULT, yes=True)
        self.assertEqual("Beta", self.client.set_feature_flag.call_args.args[0].name)

    def test_ffset_envelope_requires_items_array(self):
        for data in ({}, {"items": {}}, {"items": None}):
            with self.subTest(data=data):
                self.write_file(dict(data, profile=ImportExportProfiles.FFSET))
                with self.assertRaises(FileOperationError):
                    transfers.import_feature_flags(None, "file", path=self.path, format_="json")
                self.get_client.assert_not_called()

    def test_default_profile_preserves_variant_value_types(self):
        for value in (None, False, 0, 1.5, "text", "", [1, False], {"color": "red"}):
            with self.subTest(value=value):
                resource = {"id": "Beta", "enabled": False,
                            "variants": [{"name": "Red", "configuration_value": value}]}
                self.write_file({"feature_management": {"feature_flags": [resource]}})
                flags = transfers._read_flags(self.path, "json", ImportExportProfiles.DEFAULT)
                self.assertEqual(resource, transfers._to_feature_management(flags[0]))

    def test_default_profile_rejects_duplicate_names_without_overwriting_file(self):
        self.write_file(["original"])
        self.client.list_feature_flags.return_value = [
            FeatureFlag(name="Beta", label="test"), FeatureFlag(name="Beta", label="production")]
        with self.assertRaisesRegex(InvalidArgumentValueError, "Multiple labels"):
            transfers.export_feature_flags(None, "file", path=self.path, format_="json", label="*", yes=True)
        with open(self.path, encoding="utf-8") as source:
            self.assertEqual(["original"], json.load(source))
        transfers.export_feature_flags(None, "file", path=self.path, format_="json", label="*",
                                       profile=ImportExportProfiles.FFSET, yes=True)
        with open(self.path, encoding="utf-8") as source:
            self.assertEqual(["test", "production"], [flag["label"] for flag in json.load(source)["items"]])

    def test_default_profile_rejects_malformed_and_mismatched_schemas(self):
        invalid = [
            [], {}, {"feature_management": []}, {"feature_management": {}},
            {"feature_management": {"feature_flags": {}}},
        ]
        entries = [
            True, {}, {"name": "Beta"}, {"id": "Beta", "name": "Beta"},
            {"id": "Beta", "label": "test"}, {"id": "Beta", "tags": {}},
            {"id": "Beta", "enabled": "true"},
            {"id": "Beta", "conditions": {"filters": []}},
            {"id": "Beta", "conditions": {"client_filters": "invalid"}},
            {"id": "Beta", "variants": [True]},
            {"id": "Beta", "variants": [{"name": "Red", "value": "raw"}]},
            {"id": "Beta", "variants": [{"name": "Red", "content_type": "text/plain"}]},
            {"id": "Beta", "unsupported": True},
        ]
        invalid.extend({"feature_management": {"feature_flags": [entry]}} for entry in entries)
        for data in invalid:
            with self.subTest(data=data):
                self.write_file(data)
                with self.assertRaises(FileOperationError):
                    transfers.import_feature_flags(None, "file", path=self.path, format_="json", yes=True)
                self.get_client.assert_not_called()

    def test_default_profile_empty_import_retains_strict_behavior(self):
        self.write_file({"feature_management": {"feature_flags": []}})
        self.client.list_feature_flags.return_value = [FeatureFlag(name="Old", label="test", etag="old")]
        transfers.import_feature_flags(None, "file", path=self.path, format_="json",
                                       label="test", strict=True, yes=True)
        self.client.delete_feature_flag.assert_called_once_with(
            name="Old", label="test", etag="old", match_condition=MatchConditions.IfNotModified)

    def test_default_profile_invalid_json_variant_requires_ffset(self):
        flag = FeatureFlag.from_dict(dict(self.resource, variants=[
            {"name": "Red", "value": "{", "content_type": "application/json"}]))
        self.client.list_feature_flags.return_value = [flag]
        with self.assertRaisesRegex(FileOperationError, "Invalid JSON value"):
            transfers.export_feature_flags(None, "file", path=self.path, format_="json", yes=True)
        self.assertFalse(os.path.exists(self.path))
        transfers.export_feature_flags(None, "file", path=self.path, format_="json",
                                       profile=ImportExportProfiles.FFSET, yes=True)
        self.assertTrue(os.path.exists(self.path))

    def test_list_flags_normalizes_null_label_and_preserves_other_filters(self):
        for label, expected in ((None, "\0"), ("", "\0"), ("\\0", "\0"),
                                ("\0", "\0"), ("*", "*"), ("test", "test")):
            with self.subTest(label=label):
                self.client.list_feature_flags.reset_mock()
                transfers._list_flags(self.client, label=label)
                self.client.list_feature_flags.assert_called_once_with(
                    name_filter="*", label_filter=expected, tags_filter=None)

    def test_legacy_import_export_command_help_still_loads(self):
        from azure.cli.core import get_default_cli

        for action in ("import", "export"):
            with self.subTest(action=action), redirect_stdout(StringIO()):
                with self.assertRaises(SystemExit) as result:
                    get_default_cli().invoke(["appconfig", "kv", action, "--help"])
                self.assertEqual(0, result.exception.code)

    def test_readonly_properties_are_not_exported_or_imported(self):
        resource = dict(self.resource, etag="old", last_modified="2026-01-01T00:00:00Z")
        self.write_file([resource])
        self.import_file(preserve_labels=True, yes=True)
        written = self.client.set_feature_flag.call_args.args[0]
        self.assertIsNone(written.etag)
        self.assertIsNone(written.last_modified)
        self.assertEqual(self.resource, transfers._serialize_flag(written))

    def test_import_overrides_label_and_tags_without_changing_source(self):
        flag = FeatureFlag.from_dict(self.resource)
        source_client = Mock()
        source_client.list_feature_flags.return_value = [flag]
        self.get_client.side_effect = [source_client, self.client]
        transfers.import_feature_flags(None, "appconfig", src_name="Source", src_feature_name="Beta*",
                                       src_label="*", src_tags=["team=app"], label="production",
                                       tags={}, yes=True)
        source_client.list_feature_flags.assert_called_once_with(
            name_filter="Beta*", label_filter="*", tags_filter=["team=app"])
        written = self.client.set_feature_flag.call_args.args[0]
        self.assertEqual("production", written.label)
        self.assertEqual({}, written.tags)
        self.assertEqual("test", flag.label)
        self.assertEqual({"team": "app"}, flag.tags)

    def test_import_defaults_to_null_label_and_retains_tags(self):
        self.write_file([self.resource])
        self.import_file(yes=True)
        written = self.client.set_feature_flag.call_args.args[0]
        self.assertIsNone(written.label)
        self.assertEqual(self.resource["tags"], written.tags)
        self.client.list_feature_flags.assert_called_once_with(
            name_filter="*", label_filter="\0", tags_filter=None)

    def test_preserving_null_and_named_labels_keeps_separate_resources(self):
        self.write_file([self.resource, dict(self.resource, label=None)])
        self.import_file(preserve_labels=True, yes=True)
        self.assertEqual(2, self.client.set_feature_flag.call_count)
        self.assertEqual(["test", None],
                         [call.args[0].label for call in self.client.set_feature_flag.call_args_list])

    def test_export_store_filters_and_preserves_labels(self):
        source_client = Mock()
        source_client.list_feature_flags.return_value = [FeatureFlag.from_dict(self.resource)]
        self.get_client.side_effect = [source_client, self.client]
        transfers.export_feature_flags(None, "appconfig", feature_name="Beta*", label="*",
                                       tags=["team=app"], dest_name="Destination",
                                       preserve_labels=True, dest_tags={"new": "tag"}, yes=True)
        source_client.list_feature_flags.assert_called_once_with(
            name_filter="Beta*", label_filter="*", tags_filter=["team=app"])
        written = self.client.set_feature_flag.call_args.args[0]
        self.assertEqual("test", written.label)
        self.assertEqual({"new": "tag"}, written.tags)

    def test_ignore_match_does_not_write_identical_flags(self):
        self.write_file([self.resource])
        self.client.list_feature_flags.return_value = [FeatureFlag.from_dict(self.resource)]
        self.import_file(preserve_labels=True, yes=True)
        self.client.set_feature_flag.assert_not_called()
        self.confirm.assert_not_called()

    def test_ignore_match_ignores_service_metadata(self):
        self.write_file([self.resource])
        existing = FeatureFlag.from_dict(self.resource)
        existing.etag = "destination-etag"
        existing.last_modified = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.client.list_feature_flags.return_value = [existing]
        self.import_file(preserve_labels=True, yes=True)
        self.client.set_feature_flag.assert_not_called()
        self.confirm.assert_not_called()

    def test_all_mode_writes_identical_flags_with_destination_etag(self):
        self.write_file([self.resource])
        existing = FeatureFlag.from_dict(dict(self.resource, etag="destination"))
        self.client.list_feature_flags.return_value = [existing]
        self.import_file(preserve_labels=True, import_mode="all", yes=True)
        self.assertEqual(MatchConditions.IfNotModified,
                         self.client.set_feature_flag.call_args.kwargs["match_condition"])
        self.assertEqual("destination", self.client.set_feature_flag.call_args.kwargs["etag"])

    def test_new_flag_uses_if_missing(self):
        self.write_file([self.resource])
        self.import_file(yes=True)
        self.assertEqual(MatchConditions.IfMissing,
                         self.client.set_feature_flag.call_args.kwargs["match_condition"])

    def test_update_detects_nested_changes_and_tag_changes(self):
        for property_, value in (("enabled", True), ("tags", {"different": "tag"}),
                                 ("telemetry", {"enabled": True})):
            with self.subTest(property_=property_):
                self.client.set_feature_flag.reset_mock()
                self.write_file([dict(self.resource, **{property_: value})])
                self.client.list_feature_flags.return_value = [FeatureFlag.from_dict(self.resource)]
                self.import_file(preserve_labels=True, yes=True)
                self.client.set_feature_flag.assert_called_once()

    def test_import_dry_run_never_writes_or_deletes_or_confirms(self):
        self.write_file([self.resource])
        self.client.list_feature_flags.return_value = [FeatureFlag(name="Other", enabled=True)]
        self.import_file(strict=True, dry_run=True)
        self.client.set_feature_flag.assert_not_called()
        self.client.delete_feature_flag.assert_not_called()
        self.confirm.assert_not_called()

    def test_export_dry_run_does_not_overwrite_file(self):
        self.write_file(["original"])
        self.client.list_feature_flags.return_value = [FeatureFlag.from_dict(self.resource)]
        transfers.export_feature_flags(None, "file", path=self.path, format_="json", dry_run=True)
        with open(self.path, encoding="utf-8") as source:
            self.assertEqual(["original"], json.load(source))
        self.confirm.assert_not_called()

    def test_empty_export_does_not_create_file(self):
        transfers.export_feature_flags(None, "file", path=self.path, format_="json", yes=True)
        self.assertFalse(os.path.exists(self.path))

    def test_strict_deletes_only_destination_scope_with_etag(self):
        self.write_file([])
        old = FeatureFlag.from_dict({"name": "Old", "label": "test", "etag": "old"})
        self.client.list_feature_flags.return_value = [old]
        self.import_file(label="test", strict=True, yes=True)
        self.client.list_feature_flags.assert_called_once_with(
            name_filter="*", label_filter="test", tags_filter=None)
        self.client.delete_feature_flag.assert_called_once_with(
            name="Old", label="test", etag="old", match_condition=MatchConditions.IfNotModified)

    def test_strict_preserving_labels_does_not_delete_other_labels(self):
        self.write_file([self.resource])
        self.client.list_feature_flags.return_value = [
            FeatureFlag(name="Old", label="test"), FeatureFlag(name="Keep", label="production")]
        self.import_file(preserve_labels=True, strict=True, yes=True)
        self.assertEqual("Old", self.client.delete_feature_flag.call_args.kwargs["name"])
        self.client.delete_feature_flag.assert_called_once()

    def test_empty_strict_preserve_labels_is_rejected(self):
        self.write_file([])
        with self.assertRaises(InvalidArgumentValueError):
            self.import_file(strict=True, preserve_labels=True)
        self.client.delete_feature_flag.assert_not_called()

    def test_duplicate_destination_identity_is_rejected_before_writes(self):
        self.write_file([self.resource, dict(self.resource, label="production")])
        with self.assertRaisesRegex(InvalidArgumentValueError, "Multiple enhanced feature flags"):
            self.import_file()
        self.client.set_feature_flag.assert_not_called()

    def test_invalid_files_fail_before_connecting(self):
        invalid = [
            {}, {"feature_management": {"feature_flags": []}}, [True], [{}],
            [{"id": "Legacy", "enabled": True}], [dict(self.resource, id="Legacy")],
            [dict(self.resource, enabled="true")], [dict(self.resource, name="bad:name")],
            [dict(self.resource, label=1)], [dict(self.resource, tags={"team": 1})],
            [dict(self.resource, conditions={"client_filters": []})],
            [dict(self.resource, variants=[{"name": "Legacy", "configuration_value": {}}])],
            [dict(self.resource, conditions="invalid")], [dict(self.resource, variants="invalid")],
            [dict(self.resource, allocation=[])], [dict(self.resource, telemetry={"enabled": "true"})],
        ]
        for data in invalid:
            with self.subTest(data=data):
                self.write_file(data)
                with self.assertRaises(FileOperationError):
                    self.import_file()
                self.get_client.assert_not_called()

    def test_missing_and_malformed_files_report_file_errors(self):
        with self.assertRaises(FileOperationError):
            self.import_file()
        with open(self.path, "w", encoding="utf-8") as target:
            target.write("{")
        with self.assertRaises(FileOperationError):
            self.import_file()

    def test_malformed_yaml_reports_file_error(self):
        with open(self.path, "w", encoding="utf-8") as target:
            target.write("[{")
        with self.assertRaises(FileOperationError):
            transfers.import_feature_flags(None, "file", path=self.path, format_="yaml")

    def test_invalid_arguments_are_rejected_without_connections(self):
        cases = [
            (transfers.import_feature_flags, {"source": "appconfig", "src_name": "Source", "profile": ImportExportProfiles.FFSET}),
            (transfers.export_feature_flags, {"destination": "appconfig", "dest_name": "Destination", "profile": ImportExportProfiles.DEFAULT}),
            (transfers.export_feature_flags, {"destination": "file", "path": self.path, "format_": "json", "profile": "appconfig/kvset"}),
            (transfers.import_feature_flags, {"source": "file"}),
            (transfers.export_feature_flags, {"destination": "appconfig"}),
            (transfers.import_feature_flags, {"source": "appservice"}),
            (transfers.import_feature_flags, {"source": "file", "path": self.path, "format_": "properties"}),
            (transfers.import_feature_flags, {"source": "file", "path": self.path, "format_": "json", "preserve_labels": True, "label": "test"}),
            (transfers.import_feature_flags, {"source": "appconfig", "src_name": "Source", "strict": True}),
            (transfers.import_feature_flags, {"source": "appconfig", "src_name": "Source", "path": self.path}),
            (transfers.import_feature_flags, {"source": "file", "path": self.path, "format_": "json", "dry_run": True, "yes": True}),
            (transfers.export_feature_flags, {"destination": "file", "path": self.path, "format_": "json", "dest_tags": {"tag": "value"}}),
        ]
        for handler, arguments in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaises((InvalidArgumentValueError, RequiredArgumentMissingError,
                                        MutuallyExclusiveArgumentError)):
                    handler(None, **arguments)
                self.get_client.assert_not_called()

    def test_service_errors_are_not_silently_ignored(self):
        self.write_file([self.resource])
        self.client.set_feature_flag.side_effect = HttpResponseError(message="conflict")
        with self.assertRaises(AzureResponseError):
            self.import_file(yes=True)
        self.client.set_feature_flag.side_effect = None
        self.client.list_feature_flags.side_effect = HttpResponseError(message="forbidden")
        with self.assertRaises(AzureResponseError):
            self.import_file(yes=True)

    def test_file_write_error_is_reported(self):
        self.client.list_feature_flags.return_value = [FeatureFlag.from_dict(self.resource)]
        with self.assertRaises(FileOperationError):
            transfers.export_feature_flags(None, "file", path=self.directory.name, format_="json", yes=True)
