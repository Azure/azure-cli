# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import MagicMock, patch


class TestGetStorageAccountInfo(unittest.TestCase):
    """Unit tests for get_storage_account_info to verify it handles None resource groups."""

    def test_returns_none_when_storage_url_is_none(self):
        """Test that None is returned when storage_account_url is None."""
        from azext_serialconsole.custom import get_storage_account_info
        scf = MagicMock()
        result = get_storage_account_info(None, scf)
        self.assertIsNone(result)
        scf.storage_accounts.get_properties.assert_not_called()

    @patch('azext_serialconsole.custom.parse_storage_account_url')
    def test_returns_none_when_storage_account_name_is_none(self, mock_parse):
        """Test that None is returned and get_properties is not called when storage
        account name cannot be parsed from URL."""
        from azext_serialconsole.custom import get_storage_account_info
        mock_parse.return_value = (None, None)
        scf = MagicMock()
        result = get_storage_account_info("https://mystorage.blob.core.windows.net/", scf)
        self.assertIsNone(result)
        scf.storage_accounts.get_properties.assert_not_called()

    @patch('azext_serialconsole.custom.parse_storage_account_url')
    def test_returns_none_when_resource_group_is_none(self, mock_parse):
        """Test that None is returned and get_properties is not called when the storage
        account resource group cannot be determined (e.g., storage account not found in
        subscription). This is the regression test for the ValueError bug when
        resource_group_name=None was passed to get_properties."""
        from azext_serialconsole.custom import get_storage_account_info
        mock_parse.return_value = ("mystorage", None)
        scf = MagicMock()
        result = get_storage_account_info("https://mystorage.blob.core.windows.net/", scf)
        self.assertIsNone(result)
        # get_properties must NOT be called with None resource group
        scf.storage_accounts.get_properties.assert_not_called()

    @patch('azext_serialconsole.custom.parse_storage_account_url')
    def test_returns_none_when_no_ip_rules(self, mock_parse):
        """Test that None is returned when storage account has no IP rules."""
        from azext_serialconsole.custom import get_storage_account_info
        mock_parse.return_value = ("mystorage", "myresourcegroup")
        scf = MagicMock()
        sa_result = MagicMock()
        sa_result.network_rule_set.ip_rules = []
        scf.storage_accounts.get_properties.return_value = sa_result
        result = get_storage_account_info("https://mystorage.blob.core.windows.net/", scf)
        self.assertIsNone(result)
        scf.storage_accounts.get_properties.assert_called_once_with("myresourcegroup", "mystorage")

    @patch('azext_serialconsole.custom.parse_storage_account_url')
    def test_returns_region_when_ip_rules_present(self, mock_parse):
        """Test that region is returned when storage account has IP rules configured."""
        from azext_serialconsole.custom import get_storage_account_info
        from azext_serialconsole._arm_endpoints import ArmEndpoints
        mock_parse.return_value = ("mystorage", "myresourcegroup")
        scf = MagicMock()
        sa_result = MagicMock()
        sa_result.network_rule_set.ip_rules = [MagicMock()]
        # Use a valid location that has a mapping
        first_location = next(iter(ArmEndpoints.region_prefix_pairings))
        sa_result.location = first_location
        scf.storage_accounts.get_properties.return_value = sa_result
        result = get_storage_account_info("https://mystorage.blob.core.windows.net/", scf)
        self.assertEqual(result, ArmEndpoints.region_prefix_pairings[first_location])
        scf.storage_accounts.get_properties.assert_called_once_with("myresourcegroup", "mystorage")


class TestParseStorageAccountUrl(unittest.TestCase):
    """Unit tests for parse_storage_account_url."""

    def test_returns_none_none_for_none_url(self):
        """Test that (None, None) is returned for None URL."""
        from azext_serialconsole.custom import parse_storage_account_url
        scf = MagicMock()
        name, rg = parse_storage_account_url(None, scf)
        self.assertIsNone(name)
        self.assertIsNone(rg)

    @patch('azext_serialconsole.custom.resource_group_from_storage_account_name')
    def test_parses_storage_account_name_from_url(self, mock_rg):
        """Test that the storage account name is correctly parsed from a URL."""
        from azext_serialconsole.custom import parse_storage_account_url
        mock_rg.return_value = "myrg"
        scf = MagicMock()
        name, rg = parse_storage_account_url("https://mystorage.blob.core.windows.net/", scf)
        self.assertEqual(name, "mystorage")
        self.assertEqual(rg, "myrg")

    @patch('azext_serialconsole.custom.resource_group_from_storage_account_name')
    def test_returns_none_resource_group_when_not_found(self, mock_rg):
        """Test that None resource group is returned when storage account not found."""
        from azext_serialconsole.custom import parse_storage_account_url
        mock_rg.return_value = None
        scf = MagicMock()
        name, rg = parse_storage_account_url("https://mystorage.blob.core.windows.net/", scf)
        self.assertEqual(name, "mystorage")
        self.assertIsNone(rg)


if __name__ == '__main__':
    unittest.main()
