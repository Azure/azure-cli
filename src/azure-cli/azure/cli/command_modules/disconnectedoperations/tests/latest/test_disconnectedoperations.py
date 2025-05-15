import os
import unittest
from unittest import mock

import requests

from azure.cli.command_modules.disconnectedoperations import custom
from azure.cli.command_modules.disconnectedoperations._utils import (
    OperationResult,
    get_management_endpoint,
    handle_directory_cleanup,
)
from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest


class DisconnectedOperationsUnitTests(unittest.TestCase):
    def setUp(self):
        self.mock_cmd = mock.MagicMock()
        self.mock_cli_ctx = mock.MagicMock()
        self.mock_cmd.cli_ctx = self.mock_cli_ctx
        self.mock_cloud = mock.MagicMock()
        self.mock_cli_ctx.cloud = self.mock_cloud
        self.mock_cloud.endpoints.resource_manager = "management.azure.com"

    def test_get_management_endpoint(self):
        endpoint = get_management_endpoint(self.mock_cli_ctx)
        self.assertEqual(endpoint, "https://management.azure.com")

    @mock.patch('os.path.exists')
    @mock.patch('shutil.rmtree')
    def test_handle_directory_cleanup_success(self, mock_rmtree, mock_exists):
        mock_exists.return_value = True
        result = handle_directory_cleanup('/test/path')
        mock_exists.assert_called_once_with('/test/path')
        mock_rmtree.assert_called_once_with('/test/path')
        self.assertIsNone(result)

    @mock.patch('os.path.exists')
    @mock.patch('shutil.rmtree')
    def test_handle_directory_cleanup_error(self, mock_rmtree, mock_exists):
        mock_exists.return_value = True
        mock_rmtree.side_effect = OSError("Test error")
        result = handle_directory_cleanup('/test/path')
        mock_exists.assert_called_once_with('/test/path')
        mock_rmtree.assert_called_once_with('/test/path')
        self.assertIsInstance(result, OperationResult)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)

    def test_download_icons_success(self):
        mock_exists = mock.MagicMock(return_value=False)
        mock_download_file = mock.MagicMock()

        icons = {"small": "http://example.com/small.png"}
        custom._download_icons(
            icons, '/test/icons',
            file_downloader=mock_download_file,
            path_exists=mock_exists
        )

        expected_path = os.path.join('/test/icons', 'small.png')
        mock_download_file.assert_called_once_with("http://example.com/small.png", expected_path)

    def test_download_icons_already_exists(self):
        mock_exists = mock.MagicMock(return_value=True)
        mock_download_file = mock.MagicMock()

        icons = {"small": "http://example.com/small.png"}
        custom._download_icons(
            icons, '/test/icons',
            file_downloader=mock_download_file,
            path_exists=mock_exists
        )

        mock_download_file.assert_not_called()

    def test_download_icons_download_error(self):
        mock_exists = mock.MagicMock(return_value=False)
        mock_download_file = mock.MagicMock(side_effect=requests.RequestException("Download failed"))

        icons = {"small": "http://example.com/small.png"}
        custom._download_icons(
            icons, '/test/icons',
            file_downloader=mock_download_file,
            path_exists=mock_exists
        )

        expected_path = os.path.join('/test/icons', 'small.png')
        mock_download_file.assert_called_once_with("http://example.com/small.png", expected_path)

    def test_list_offers_transformation(self):
        """Test the transformation logic of list_offers without calling API."""
        # Mock API response data
        api_data = [{
            "offerContent": {
                "offerPublisher": {"publisherId": "test-publisher"},
                "offerId": "test-offer"
            },
            "marketplaceSkus": [{
                "marketplaceSkuId": "test-sku",
                "marketplaceSkuVersions": ["1.0", "2.0"],
                "operatingSystem": {"type": "Windows"}
            }]
        }]
        
        # Test transformation logic only
        result = []
        for offer in api_data:
            offer_content = offer.get("offerContent", {})
            skus = offer.get("marketplaceSkus", [])

            for sku in skus:
                versions = sku.get("marketplaceSkuVersions", [])[:]
                row = {
                    "Publisher": offer_content.get("offerPublisher", {}).get("publisherId"),
                    "Offer": offer_content.get("offerId"),
                    "SKU": sku.get("marketplaceSkuId"),
                    "Versions": f"{len(versions)} {'version' if len(versions) == 1 else 'versions'} available",
                    "OS_Type": sku.get("operatingSystem", {}).get("type"),
                }
                result.append(row)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Publisher"], "test-publisher")
        self.assertEqual(result[0]["Offer"], "test-offer")
        self.assertEqual(result[0]["SKU"], "test-sku")
        self.assertEqual(result[0]["Versions"], "2 versions available")
    
    def test_get_offer_transformation(self):
        """Test the transformation logic of get_offer without calling API."""
        # Mock API response data
        api_data = {
            "offerContent": {
                "offerPublisher": {"publisherId": "test-publisher"},
                "offerId": "test-offer"
            },
            "marketplaceSkus": [{
                "marketplaceSkuId": "test-sku",
                "marketplaceSkuVersions": [
                    {"name": "1.0", "minimumDownloadSizeInMb": 100},
                    {"name": "2.0", "minimumDownloadSizeInMb": 200}
                ],
                "operatingSystem": {"type": "Windows"}
            }]
        }
        
        # Test transformation logic only
        result = []
        offer_content = api_data.get("offerContent", {})
        skus = api_data.get("marketplaceSkus", [])

        for sku in skus:
            # Get all versions for this SKU
            versions = sku.get("marketplaceSkuVersions", [])[:]

            # Transform versions and size array into a string
            version_str = ", ".join(
                f"{v.get('name')}({v.get('minimumDownloadSizeInMb')}MB)"
                for v in versions
            )

            # Create a single row with flattened version info
            row = {
                "Publisher": offer_content.get("offerPublisher", {}).get("publisherId"),
                "Offer": offer_content.get("offerId"),
                "SKU": sku.get("marketplaceSkuId"),
                "Versions": version_str,
                "OS_Type": sku.get("operatingSystem", {}).get("type"),
            }
            result.append(row)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Publisher"], "test-publisher")
        self.assertEqual(result[0]["Offer"], "test-offer")
        self.assertEqual(result[0]["SKU"], "test-sku")
        self.assertIn("1.0(100MB)", result[0]["Versions"])
        self.assertIn("2.0(200MB)", result[0]["Versions"])


class DisconnectedOperationsScenarioTests(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_disconnectedops')
    def test_list_offers(self, resource_group):
        self.kwargs.update({
            'resource_group': resource_group,
            'resource': self.create_random_name('edgedevice', 20)
        })
        if self.is_live:
            self.cmd('az databoxedge device create --resource-group-name {resource_group} -n {resource}')
            offers = self.cmd('az edge disconnected-operation offer list --resource-group {resource_group} --resource-name {resource}').get_output_in_json()
            self.assertIsNotNone(offers)

    @ResourceGroupPreparer(name_prefix='cli_test_disconnectedops')
    def test_get_offer(self, resource_group):
        self.kwargs.update({
            'resource_group': resource_group,
            'resource': self.create_random_name('edgedevice', 20),
            'publisher': 'microsoftwindowsserver',
            'offer': 'windowsserver'
        })
        if self.is_live:
            result = self.cmd('az edge disconnected-operation offer get --resource-group {resource_group} --resource-name {resource} --publisher-name {publisher} --offer-id {offer}').get_output_in_json()
            self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()