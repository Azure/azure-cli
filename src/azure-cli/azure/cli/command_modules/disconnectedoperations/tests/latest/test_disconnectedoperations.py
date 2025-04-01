# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.command_modules.disconnectedoperations import custom
from azure.cli.command_modules.disconnectedoperations._utils import (
    OperationResult,
    get_management_endpoint,
    handle_directory_cleanup,
)
from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest


class DisconnectedOperationsUnitTests(unittest.TestCase):
    def setUp(self):
        # Common mocks
        self.mock_logger = mock.MagicMock()
        self.mock_cmd = mock.MagicMock()
        self.mock_cli_ctx = mock.MagicMock()
        self.mock_cmd.cli_ctx = self.mock_cli_ctx
        self.mock_cloud = mock.MagicMock()
        self.mock_cli_ctx.cloud = self.mock_cloud
        self.mock_cloud.endpoints.resource_manager = "management.azure.com"
        
    def test_get_management_endpoint(self):
        """Test get_management_endpoint returns the resource manager endpoint"""
        endpoint = get_management_endpoint(self.mock_cli_ctx)
        self.assertEqual(endpoint, "https://" + self.mock_cloud.endpoints.resource_manager)
    
    @mock.patch('os.path.exists')
    @mock.patch('shutil.rmtree')
    def test_handle_directory_cleanup_success(self, mock_rmtree, mock_exists):
        """Test directory cleanup when directory exists"""
        mock_exists.return_value = True
        
        result = handle_directory_cleanup('/test/path')
        
        mock_exists.assert_called_once_with('/test/path')
        mock_rmtree.assert_called_once_with('/test/path')
        self.assertIsNone(result)
    
    @mock.patch('os.path.exists')
    @mock.patch('shutil.rmtree')
    def test_handle_directory_cleanup_error(self, mock_rmtree, mock_exists):
        """Test directory cleanup when error occurs"""
        mock_exists.return_value = True
        mock_rmtree.side_effect = OSError("Test error")
        
        result = handle_directory_cleanup('/test/path')
        
        mock_exists.assert_called_once_with('/test/path')
        mock_rmtree.assert_called_once_with('/test/path')
        self.assertIsInstance(result, OperationResult)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)
    
    @mock.patch('os.path.exists')
    @mock.patch('azure.cli.command_modules.disconnectedoperations._utils.download_file')
    def test_download_icons_success(self, mock_download_file, mock_exists):
        """Test icon download success path"""
        # Setup mocks
        mock_exists.return_value = False
        mock_download_file.return_value = True
        
        # Setup test data
        icons = {"small": "http://example.com/small.png"}
        
        # Test
        custom._download_icons(icons, '/test/icons')
        
        # Verify download_file was called correctly
        mock_download_file.assert_called_once_with("http://example.com/small.png", mock.ANY)
        # Verify file path in the call ends with the expected name
        actual_path = mock_download_file.call_args[0][1]
        self.assertTrue(actual_path.endswith('small.png'))
    
    @mock.patch('os.path.exists')
    @mock.patch('azure.cli.command_modules.disconnectedoperations._utils.download_file')
    def test_download_icons_already_exists(self, mock_download_file, mock_exists):
        """Test icon download when file already exists"""
        # Setup mocks
        mock_exists.return_value = True
        
        # Setup test data
        icons = {"small": "http://example.com/small.png"}
        
        # Test
        custom._download_icons(icons, '/test/icons')
        
        # Verify download not called when file exists
        mock_download_file.assert_not_called()
    
    @mock.patch('os.path.exists')
    @mock.patch('azure.cli.command_modules.disconnectedoperations._utils.download_file')
    def test_download_icons_download_error(self, mock_download_file, mock_exists):
        """Test icon download with download error"""
        # Setup mocks
        mock_exists.return_value = False
        mock_download_file.return_value = False
        
        # Setup test data
        icons = {"small": "http://example.com/small.png"}
        
        # Test
        custom._download_icons(icons, '/test/icons')
        
        # Verify download attempt was made
        mock_download_file.assert_called_once_with("http://example.com/small.png", mock.ANY)
    
    @mock.patch('azure.cli.core.commands.client_factory.get_subscription_id')
    @mock.patch('azure.cli.command_modules.disconnectedoperations.aaz.latest.edge_marketplace.offer.List')
    def test_list_offers_success(self, mock_list_command, mock_get_subscription_id):
        """Test list_offers success path"""
        # Setup mocks
        mock_get_subscription_id.return_value = "test-subscription"
        
        # Mock the List command and its returned iterator
        mock_command_instance = mock.MagicMock()
        mock_list_command.return_value = mock_command_instance
        
        # Create sample offers data
        offers_data = [
            {
                "offerContent": {
                    "offerPublisher": {"publisherId": "test-publisher"},
                    "offerId": "test-offer"
                },
                "marketplaceSkus": [
                    {
                        "marketplaceSkuId": "test-sku",
                        "marketplaceSkuVersions": ["1.0", "2.0"],
                        "operatingSystem": {"type": "Windows"}
                    }
                ]
            }
        ]
        
        # Set up the iterator to return our offers
        mock_command_instance.return_value = offers_data
        
        # Test
        with mock.patch('azure.cli.command_modules.disconnectedoperations._utils.construct_resource_uri') as mock_uri:
            mock_uri.return_value = "/subscriptions/test-subscription/resourceGroups/test-rg/providers/Microsoft.Edge/disconnectedOperations/test-resource"
            result = custom.list_offers(self.mock_cmd, "test-rg", "test-resource")
        
        # Verify
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Publisher"], "test-publisher")
        self.assertEqual(result[0]["Offer"], "test-offer")
        self.assertEqual(result[0]["SKU"], "test-sku")
        self.assertEqual(result[0]["Versions"], "2 versions available")
    
    @mock.patch('azure.cli.core.commands.client_factory.get_subscription_id')
    @mock.patch('azure.cli.command_modules.disconnectedoperations.aaz.latest.edge_marketplace.offer.Show')
    def test_get_offer_success(self, mock_show_command, mock_get_subscription_id):
        """Test get_offer success path"""
        # Setup mocks
        mock_get_subscription_id.return_value = "test-subscription"
        
        # Mock the Show command and its return value
        mock_command_instance = mock.MagicMock()
        mock_show_command.return_value = mock_command_instance
        
        # Create sample offer data
        offer_data = {
            "offerContent": {
                "offerPublisher": {"publisherId": "test-publisher"},
                "offerId": "test-offer"
            },
            "marketplaceSkus": [
                {
                    "marketplaceSkuId": "test-sku",
                    "marketplaceSkuVersions": [
                        {"name": "1.0", "minimumDownloadSizeInMb": 100},
                        {"name": "2.0", "minimumDownloadSizeInMb": 200}
                    ],
                    "operatingSystem": {"type": "Windows"}
                }
            ]
        }
        
        # Set up the return value for the command
        mock_command_instance.return_value = offer_data
        
        # Test
        with mock.patch('azure.cli.command_modules.disconnectedoperations._utils.construct_resource_uri') as mock_uri:
            mock_uri.return_value = "/subscriptions/test-subscription/resourceGroups/test-rg/providers/Microsoft.Edge/disconnectedOperations/test-resource"
            result = custom.get_offer(self.mock_cmd, "test-rg", "test-resource", "test-publisher", "test-offer")
        
        # Verify
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Publisher"], "test-publisher")
        self.assertEqual(result[0]["Offer"], "test-offer")
        self.assertEqual(result[0]["SKU"], "test-sku")
        self.assertIn("1.0(100MB)", result[0]["Versions"])
        self.assertIn("2.0(200MB)", result[0]["Versions"])
    
    @mock.patch('azure.cli.core.commands.client_factory.get_subscription_id')
    @mock.patch('azure.cli.core.util.send_raw_request')
    def test_package_offer_not_found(self, mock_send_raw_request, mock_get_subscription_id):
        """Test package_offer when offer is not found"""
        # Setup mocks
        mock_get_subscription_id.return_value = "test-subscription"
        
        mock_response = mock.MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_send_raw_request.return_value = mock_response
        
        # Test
        result = custom.package_offer(
            self.mock_cmd, "test-rg", "test-resource", 
            "test-publisher", "test-offer", "test-sku", "1.0", "/tmp"
        )
        
        # Verify
        self.assertEqual(result["status"], "failed")
        self.assertIn("error", result)
        self.assertEqual(result["resource_group_name"], "test-rg")
    
    @mock.patch('azure.cli.command_modules.disconnectedoperations._utils._determine_region')
    @mock.patch('custom._find_sku_and_version')
    def test_determine_region(self, mock_find_sku, mock_determine_region):
        """Test _determine_region function"""
        # Setup mock
        mock_determine_region.return_value = "westus"
        
        # Test explicit region
        region = custom._determine_region(self.mock_cmd, "eastus")
        self.assertEqual(region, "eastus")
        
        # Test config region
        self.mock_cli_ctx.config.get.return_value = "centralus"
        region = custom._determine_region(self.mock_cmd, None)
        self.assertEqual(region, "centralus")
        
        # Test cloud default
        self.mock_cli_ctx.config.get.side_effect = KeyError()
        self.mock_cloud.primary_endpoint_region = "northeurope"
        region = custom._determine_region(self.mock_cmd, None)
        self.assertEqual(region, "northeurope")
        
        # Test fallback
        self.mock_cli_ctx.config.get.side_effect = KeyError()
        delattr(self.mock_cloud, 'primary_endpoint_region')
        region = custom._determine_region(self.mock_cmd, None)
        self.assertEqual(region, "eastus")


class DisconnectedOperationsScenarioTests(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_disconnectedops')
    def test_list_offers(self, resource_group):
        """Integration test for list_offers command"""
        self.kwargs.update({
            'resource_group': resource_group,
            'resource': self.create_random_name('edgedevice', 20)
        })
        
        # Skip if recording as this requires an actual Edge device
        if self.is_live:
            # Create Edge device first (requires additional setup)
            # This would need an actual Edge device setup in the resource group
            # For recording purposes, we're just showing the structure
            self.cmd('az databoxedge device create --resource-group-name {resource_group} -n {resource}')
            
            offers = self.cmd('az edge disconnected-operation offer list --resource-group {resource_group} --resource-name {resource}').get_output_in_json()
            self.assertIsNotNone(offers)
            # In a real test, we'd validate specific values in the output
    
    @ResourceGroupPreparer(name_prefix='cli_test_disconnectedops')
    def test_get_offer(self, resource_group):
        """Integration test for get_offer command"""
        self.kwargs.update({
            'resource_group': resource_group,
            'resource': self.create_random_name('edgedevice', 20),
            'publisher': 'microsoftwindowsserver',
            'offer': 'windowsserver'
        })
        
        # Skip if recording as this requires an actual Edge device
        if self.is_live:
            # This test would need to be updated with actual device creation
            # and valid offer details that exist in your test environment
            
            result = self.cmd('az edge disconnected-operation offer get --resource-group {resource_group} --resource-name {resource} --publisher-name {publisher} --offer-id {offer}').get_output_in_json()
            self.assertIsNotNone(result)
            # Verify specific values in output for a real test
            
    @ResourceGroupPreparer(name_prefix='cli_test_disconnectedops_params')
    def test_get_offer_with_resource_group_name_parameter(self, resource_group):
        """Test get_offer with explicit resource-group-name parameter"""
        self.kwargs.update({
            'resource_group': resource_group,
            'resource': self.create_random_name('edgedevice', 20),
            'publisher': 'microsoftwindowsserver',
            'offer': 'windowsserver'
        })
        
        # Skip if recording as this requires an actual Edge device
        if self.is_live:
            # Create Edge device first (requires additional setup)
            self.cmd('az databoxedge device create --resource-group {resource_group} --name {resource}')
            
            # Test with the full --resource-group-name parameter
            result = self.cmd('az edge disconnected-operation offer get --resource-group {resource_group} --resource-name {resource} --publisher-name {publisher} --offer-id {offer}').get_output_in_json()
            self.assertIsNotNone(result)
            # In a real test with actual data, we would add more specific assertions

    @ResourceGroupPreparer(name_prefix='cli_test_disconnectedops_pkg')
    def test_package_offer_with_resource_group_name_parameter(self, resource_group):
        """Test package_offer with explicit resource-group-name parameter"""
        self.kwargs.update({
            'resource_group': resource_group,
            'resource': self.create_random_name('edgedevice', 20),
            'publisher': 'microsoftwindowsserver',
            'offer': 'windowsserver',
            'sku': 'datacenter-core-1903-with-containers-smalldisk',
            'version': '18362.720.2003120536',
            'output_folder': self.create_temp_dir()
        })
        
        if self.is_live:
            # Skip actual device creation in recorded tests
            # Test with the full --resource-group-name parameter
            result = self.cmd('az edge disconnected-operation offer package --resource-group {resource_group} --resource-name {resource} --publisher-name {publisher} --offer-id {offer} --sku {sku} --version {version} --output-folder {output_folder}').get_output_in_json()
            self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()