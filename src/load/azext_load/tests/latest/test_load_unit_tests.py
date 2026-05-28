# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import unittest
from unittest import mock


# Mock modules needed by utils.py before importing it
# This avoids needing the full extension infrastructure installed
_mock_modules = {
    'azext_load.data_plane.utils.constants': mock.MagicMock(),
    'azext_load.data_plane.utils.validators': mock.MagicMock(),
    'azext_load.data_plane.utils.utils_yaml_config': mock.MagicMock(),
    'azext_load.vendored_sdks': mock.MagicMock(),
    'azext_load.vendored_sdks.loadtesting_mgmt': mock.MagicMock(),
}
_mock_modules['azext_load.data_plane.utils.constants'].LoadTestConfigKeys = mock.MagicMock()
_mock_modules['azext_load.data_plane.utils.constants'].LoadTestTrendsKeys = mock.MagicMock()
_mock_modules['azext_load.vendored_sdks.loadtesting_mgmt'].LoadTestMgmtClient = mock.MagicMock()


class TestUploadPropertiesFileHelperNullFix(unittest.TestCase):
    """
    Unit tests for the fix to 'NoneType' object has no attribute 'get' error
    in upload_properties_file_helper when YAML config has 'properties: null'.

    Issue: https://github.com/Azure/azure-cli/issues/32748

    Root cause: When a YAML config file has 'properties: null', the call
    yaml_data.get("properties", {}) returns None (not {}) because the key
    exists with a None value. The fix uses (yaml_data.get("properties") or {})
    which correctly returns {} when the value is None.
    """

    def test_null_properties_does_not_raise_attribute_error(self):
        """
        When yaml_data has 'properties: null', calling
        yaml_data.get("properties", {}).get("userPropertyFile") raises AttributeError.
        The fix (yaml_data.get("properties") or {}).get("userPropertyFile") should not raise.
        """
        yaml_data = {"properties": None, "testPlan": "test.jmx"}

        # Demonstrate the bug: get with default does NOT help when key exists with None value
        properties_old = yaml_data.get("properties", {})
        self.assertIsNone(properties_old)  # Returns None, not {} - this is the bug!

        # Verify the fix works correctly
        properties_fixed = (yaml_data.get("properties") or {})
        self.assertEqual(properties_fixed, {})  # Returns {} as expected

        # Verify the fix doesn't raise AttributeError
        user_prop_file = (yaml_data.get("properties") or {}).get("userPropertyFile")
        self.assertIsNone(user_prop_file)

    def test_absent_properties_key_works(self):
        """When 'properties' key is absent, the fix still works correctly."""
        yaml_data = {"testPlan": "test.jmx"}

        result = (yaml_data.get("properties") or {}).get("userPropertyFile")
        self.assertIsNone(result)

    def test_valid_properties_dict_works(self):
        """When 'properties' is a valid dict, the fix preserves normal behavior."""
        yaml_data = {
            "properties": {"userPropertyFile": "test.properties"},
            "testPlan": "test.jmx"
        }

        result = (yaml_data.get("properties") or {}).get("userPropertyFile")
        self.assertEqual(result, "test.properties")

    def test_upload_properties_file_helper_with_null_properties(self):
        """
        Integration test: upload_properties_file_helper should not raise
        AttributeError when yaml_data has 'properties: null'.
        """
        with mock.patch.dict(sys.modules, _mock_modules):
            from azext_load.data_plane.utils.utils import upload_properties_file_helper

            yaml_data = {"properties": None, "testPlan": "test.jmx"}
            client = mock.MagicMock()
            existing_test_files = []

            with mock.patch(
                "azext_load.data_plane.utils.utils.upload_generic_files_helper"
            ) as mock_upload:
                # This should NOT raise AttributeError: 'NoneType' object has no attribute 'get'
                upload_properties_file_helper(
                    client=client,
                    test_id="test-id",
                    yaml_data=yaml_data,
                    load_test_config_file="test.yaml",
                    existing_test_files=existing_test_files,
                    wait=False
                )
                # With properties=None, userPropertyFile is None, so no upload should happen
                mock_upload.assert_not_called()

    def test_upload_properties_file_helper_with_valid_properties(self):
        """
        Integration test: upload_properties_file_helper should upload the user
        property file when yaml_data has a valid userPropertyFile value.
        """
        with mock.patch.dict(sys.modules, _mock_modules):
            from azext_load.data_plane.utils.utils import upload_properties_file_helper

            yaml_data = {"properties": {"userPropertyFile": "user.properties"}}
            client = mock.MagicMock()
            existing_test_files = []

            with mock.patch(
                "azext_load.data_plane.utils.utils.upload_generic_files_helper"
            ) as mock_upload:
                upload_properties_file_helper(
                    client=client,
                    test_id="test-id",
                    yaml_data=yaml_data,
                    load_test_config_file="test.yaml",
                    existing_test_files=existing_test_files,
                    wait=False
                )
                mock_upload.assert_called_once()
                call_kwargs = mock_upload.call_args.kwargs
                self.assertEqual(call_kwargs["file_to_upload"], "user.properties")

    def test_upload_properties_file_helper_with_no_properties(self):
        """
        Integration test: upload_properties_file_helper should not upload anything
        when yaml_data has no 'properties' key.
        """
        with mock.patch.dict(sys.modules, _mock_modules):
            from azext_load.data_plane.utils.utils import upload_properties_file_helper

            yaml_data = {"testPlan": "test.jmx"}
            client = mock.MagicMock()
            existing_test_files = []

            with mock.patch(
                "azext_load.data_plane.utils.utils.upload_generic_files_helper"
            ) as mock_upload:
                upload_properties_file_helper(
                    client=client,
                    test_id="test-id",
                    yaml_data=yaml_data,
                    load_test_config_file="test.yaml",
                    existing_test_files=existing_test_files,
                    wait=False
                )
                mock_upload.assert_not_called()


if __name__ == "__main__":
    unittest.main()
