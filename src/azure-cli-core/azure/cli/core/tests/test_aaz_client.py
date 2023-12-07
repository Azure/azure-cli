# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock
from azure.cli.core.aaz._command_ctx import AAZCommandCtx
from azure.cli.core.aaz import AAZArgumentsSchema
from azure.cli.core.mock import DummyCli
import tempfile

_METADATA = [
    {
        "name": "TestCloud",
        "portal": "https://portal.azure.com.test",
        "authentication": {
            "loginEndpoint": "https://login.microsoftonline.com.test/",
            "audiences": [
                "https://management.core.windows.net.test/",
                "https://management.azure.com.test/"
            ],
            "tenant": "common.test",
            "identityProvider": "AAD.test"
        },
        "media": "https://rest.media.azure.net.test",
        "graphAudience": "https://graph.windows.net.test/",
        "graph": "https://graph.windows.net.test/",
        "suffixes": {
            "azureDataLakeStoreFileSystem": "azuredatalakestore.net.test",
            "acrLoginServer": "azurecr.io.test",
            "sqlServerHostname": "database.windows.net.test",
            "azureDataLakeAnalyticsCatalogAndJob": "azuredatalakeanalytics.net.test",
            "keyVaultDns": "vault.azure.net.test",
            "storage": "core.windows.net.test",
            "azureFrontDoorEndpointSuffix": "azurefd.net.test",
            "notExist": "notExistSuffix.test",
        },
        "batch": "https://batch.core.windows.net.test/",
        "resourceManager": "https://management.azure.com.test/",
        "vmImageAliasDoc": "https://raw.githubusercontent.com.test/Azure/azure-rest-api-specs/master/arm-compute/quickstart-templates/aliases.json",
        "activeDirectoryDataLake": "https://datalake.azure.net.test/",
        "sqlManagement": "https://management.core.windows.net.test:8443/",
        "gallery": "https://gallery.azure.com.test/",
        "notExist": {
            "Special": "https://notexist.azure.com.test/",
        }
    }
]


class TestAAZCommandCtx(unittest.TestCase):

    @mock.patch('azure.cli.core.cloud.retrieve_arm_cloud_metadata', return_value=_METADATA)
    @mock.patch('azure.cli.core.cloud.CLOUD_CONFIG_FILE', tempfile.mkstemp()[1])
    @mock.patch('azure.cli.core.cloud.GLOBAL_CONFIG_DIR', tempfile.mkdtemp())
    @mock.patch.dict('os.environ', {'ARM_CLOUD_METADATA_URL': 'https://management.azure.com/metadata/endpoints?api-version=2019-05-01'})
    def test_retrieve_value_in_arm_cloud_metadata(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZBaseClient
        from azure.cli.core.cloud import get_active_cloud_name, refresh_known_clouds, _set_active_cloud, CloudSuffixes, CloudEndpoints
        from azure.cli.core.aaz import AAZStrArg
        from azure.cli.core.aaz import exceptions
        schema = AAZArgumentsSchema()
        schema.region = AAZStrArg()
        region = "global"
        ctx = AAZCommandCtx(
            cli_ctx=DummyCli(random_config_dir=True),
            schema=schema,
            command_args={
                "region": region,
            }
        )
        refresh_known_clouds()
        self.assertEqual(get_active_cloud_name(ctx.cli_ctx), 'AzureCloud')

        self.assertEqual(
            AAZBaseClient._retrieve_value_in_arm_cloud_metadata(ctx, "notExist.Special"),
            None)

        _set_active_cloud(ctx.cli_ctx, 'TestCloud')

        self.assertEqual(get_active_cloud_name(ctx.cli_ctx), 'TestCloud')
        self.assertEqual(
            AAZBaseClient._retrieve_value_in_arm_cloud_metadata(ctx, "suffixes.azureDataLakeStoreFileSystem"),
            "azuredatalakestore.net.test")
        self.assertEqual(
            AAZBaseClient._retrieve_value_in_arm_cloud_metadata(ctx, "notExist.Special"),
            "https://notexist.azure.com.test/")
        self.assertEqual(
            AAZBaseClient._retrieve_value_in_arm_cloud_metadata(ctx, "authentication.audiences[0]"),
            "https://management.core.windows.net.test/")
        self.assertEqual(
            AAZBaseClient._retrieve_value_in_arm_cloud_metadata(ctx, "authentication.audiences[100]"),
            None)
        self.assertEqual(
            AAZBaseClient._retrieve_value_in_arm_cloud_metadata(ctx, "authentication.audiences100"),
            None)

        with self.assertRaises(TypeError):
            AAZBaseClient._retrieve_value_in_arm_cloud_metadata(ctx, "authentication.audiences.1")

        with self.assertRaises(exceptions.AAZInvalidShorthandSyntaxError):
            AAZBaseClient._retrieve_value_in_arm_cloud_metadata(ctx, "authentication.audiences[0")

        for arm_idx in CloudSuffixes.ARM_METADATA_INDEX.values():
            value = AAZBaseClient.get_cloud_suffix(ctx, arm_idx)
            self.assertTrue(value is None or value.startswith("."))

        self.assertEqual(AAZBaseClient.get_cloud_suffix(ctx, "suffixes.notExist"),
                         ".notExistSuffix.test")

        for arm_idx in CloudEndpoints.ARM_METADATA_INDEX.values():
            value = AAZBaseClient.get_cloud_endpoint(ctx, arm_idx)
            self.assertTrue(value is None or value.startswith("https://"))

        self.assertEqual(AAZBaseClient.get_cloud_endpoint(ctx, "notExist.Special"),
                         "https://notexist.azure.com.test/")
