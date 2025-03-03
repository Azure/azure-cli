# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

import requests

from azure.cli.command_modules.disconnectedoperations import custom
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
        """Test _get_management_endpoint returns the resource manager endpoint"""
        endpoint = custom._get_management_endpoint(self.mock_cli_ctx)
        self.assertEqual(endpoint, self.mock_cloud.endpoints.resource_manager)
    
    @mock.patch('os.path.exists')
    @mock.patch('shutil.rmtree')
    def test_handle_directory_cleanup_success(self, mock_rmtree, mock_exists):
        """Test directory cleanup when directory exists"""
        mock_exists.return_value = True
        
        result = custom._handle_directory_cleanup('/test/path', self.mock_logger)
        
        mock_exists.assert_called_once_with('/test/path')
        mock_rmtree.assert_called_once_with('/test/path')
        self.mock_logger.info.assert_called_once()
        self.assertIsNone(result)
    
    @mock.patch('os.path.exists')
    @mock.patch('shutil.rmtree')
    def test_handle_directory_cleanup_error(self, mock_rmtree, mock_exists):
        """Test directory cleanup when error occurs"""
        mock_exists.return_value = True
        mock_rmtree.side_effect = OSError("Test error")
        
        result = custom._handle_directory_cleanup('/test/path', self.mock_logger)
        
        mock_exists.assert_called_once_with('/test/path')
        mock_rmtree.assert_called_once_with('/test/path')
        self.mock_logger.error.assert_called_once()
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "failed")
        self.assertIn("error", result)
    
    @mock.patch('os.path.exists')
    @mock.patch('requests.get')
    def test_download_icons_success(self, mock_get, mock_exists):
        """Test icon download success path"""
        # Setup mocks
        mock_exists.return_value = False
        
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake_image_content"
        mock_get.return_value = mock_response
        
        # Setup test data
        icons = {"small": "http://example.com/small.png"}
        
        # Mock open to avoid actual file operations
        m = mock.mock_open()
        with mock.patch('builtins.open', m):
            custom._download_icons(icons, '/test/icons', self.mock_logger)
        
        # Verify - using platform-independent path comparison
        mock_get.assert_called_once_with("http://example.com/small.png")
        
        # Get the actual file path from the mock call
        actual_call = m.call_args
        actual_path = actual_call[0][0]
        actual_mode = actual_call[0][1]
        
        # Verify the mode is correct
        self.assertEqual(actual_mode, 'wb')
        
        # Verify path ends with the expected path (using platform-independent comparison)
        expected_end = 'small.png'
        print(actual_path)
        self.assertTrue(actual_path.endswith(expected_end))
        
        # Verify file write was called with correct content
        handle = m()
        handle.write.assert_called_once_with(b"fake_image_content")
        self.mock_logger.info.assert_called_once()
    
    @mock.patch('os.path.exists')
    @mock.patch('requests.get')
    def test_download_icons_request_error(self, mock_get, mock_exists):
        """Test icon download with request error"""
        # Setup mocks
        mock_exists.return_value = False
        mock_get.side_effect = requests.RequestException("Connection error")  # Use the imported requests module
        
        # Setup test data
        icons = {"small": "http://example.com/small.png"}
        
        # Test
        custom._download_icons(icons, '/test/icons', self.mock_logger)
        
        # Verify
        mock_get.assert_called_once_with("http://example.com/small.png")
        self.mock_logger.error.assert_called_once()
    
    @mock.patch('azure.cli.core.commands.client_factory.get_subscription_id')
    @mock.patch('azure.cli.core.util.send_raw_request')
    def test_list_offers_success(self, mock_send_raw_request, mock_get_subscription_id):
        """Test list_offers success path"""
        # Setup mocks
        mock_get_subscription_id.return_value = "test-subscription"
        
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [
                {
                    "properties": {
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
                }
            ]
        }
        mock_send_raw_request.return_value = mock_response
        
        # Test
        result = custom.list_offers(self.mock_cmd, "test-rg", "test-resource")
        
        # Verify
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Publisher"], "test-publisher")
        self.assertEqual(result[0]["Offer"], "test-offer")
        self.assertEqual(result[0]["SKU"], "test-sku")
        self.assertEqual(result[0]["Versions"], "2 versions available")
    
    @mock.patch('azure.cli.core.commands.client_factory.get_subscription_id')
    @mock.patch('azure.cli.core.util.send_raw_request')
    def test_get_offer_success(self, mock_send_raw_request, mock_get_subscription_id):
        """Test get_offer success path"""
        # Setup mocks
        mock_get_subscription_id.return_value = "test-subscription"
        
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "properties": {
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
        }
        mock_send_raw_request.return_value = mock_response
        
        # Test
        result = custom.get_offer(self.mock_cmd, "test-rg", "test-resource", "test-publisher", "test-offer")
        
        # Verify
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Publisher"], "test-publisher")
        self.assertEqual(result[0]["Offer"], "test-offer")
        self.assertEqual(result[0]["SKU"], "test-sku")
        self.assertIn("1.0(100MB)", result[0]["Versions"])
    
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
            
            offers = self.cmd('az disconnectedoperations edgemarketplace listoffer --resource-group-name {resource_group} --resource-name {resource}').get_output_in_json()
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
            
            result = self.cmd('az disconnectedoperations edgemarketplace getoffer --resource-group-name {resource_group} --resource-name {resource} --publisher-name {publisher} --offer-name {offer}').get_output_in_json()
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
            self.cmd('az databoxedge device create --resource-group-name {resource_group} --name {resource}')
            
            # Test with the full --resource-group-name parameter
            result = self.cmd('az disconnectedoperations edgemarketplace getoffer --resource-group-name {resource_group} --resource-name {resource} --publisher-name {publisher} --offer-name {offer}').get_output_in_json()
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
            result = self.cmd('az disconnectedoperations edgemarketplace packageoffer --resource-group-name {resource_group} --resource-name {resource} --publisher-name {publisher} --offer-name {offer} --sku {sku} --version {version} --output-folder {output_folder}').get_output_in_json()
            self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()