# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest.mock import Mock, patch

from azure.cli.command_modules.acs.azuremonitormetrics.amw.defaults import (
    get_default_mac_name_and_region, 
    get_default_mac_region
)

class TestAMWDefaults(unittest.TestCase):
    @patch('azure.cli.command_modules.acs.azuremonitormetrics.amw.defaults.get_supported_rp_locations')
    def test_get_default_mac_region(self, mock_get_supported_rp_locations):
        mock_get_supported_rp_locations.return_value = ["eastus", "westus"]

        self.assertEqual(get_default_mac_region(
            cmd=None, cluster_region='eastus', subscription='test_subscription'
        ), 'eastus')
        self.assertEqual(get_default_mac_region(
            cmd=None, cluster_region='centraluseuap', subscription='test_subscription'
        ), 'eastus2euap')
        self.assertEqual(get_default_mac_region(
            cmd=None, cluster_region='nonexistent', subscription='test_subscription'
        ), 'eastus')

    def test_get_default_mac_name_and_region(self):
        with patch('azure.cli.command_modules.acs.azuremonitormetrics.amw.defaults.get_default_mac_region') as mock_get_default_mac_region:
            mock_get_default_mac_region.return_value = 'eastus'

            default_mac_name, default_mac_region = get_default_mac_name_and_region(
                cmd=None, cluster_region='eastus', subscription='test_subscription'
            )

            self.assertEqual(default_mac_name, 'DefaultAzureMonitorWorkspace-eastus')
            self.assertEqual(default_mac_region, 'eastus')

if __name__ == '__main__':
    unittest.main()
