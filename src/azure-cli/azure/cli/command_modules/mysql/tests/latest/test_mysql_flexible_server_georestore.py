# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from azure.cli.command_modules.mysql.custom import flexible_server_georestore


class FlexibleServerGeoRestoreUnitTest(unittest.TestCase):

    @patch('azure.cli.command_modules.mysql.custom.sdk_no_wait')
    @patch('azure.cli.command_modules.mysql.custom.resolve_poller')
    @patch('azure.cli.command_modules.mysql.custom.flexible_server_provision_network_resource')
    @patch('azure.cli.command_modules.mysql.custom._determine_iops')
    @patch('azure.cli.command_modules.mysql.custom.get_identity_and_data_encryption')
    @patch('azure.cli.command_modules.mysql.custom.validate_server_name')
    @patch('azure.cli.command_modules.mysql.custom.get_mysql_list_skus_info')
    @patch('azure.cli.command_modules.mysql.custom.get_mysql_flexible_management_client_by_sub')
    @patch('azure.cli.command_modules.mysql.custom.parse_resource_id')
    @patch('azure.cli.command_modules.mysql.custom.is_valid_resource_id')
    @patch('azure.cli.command_modules.mysql.custom.models.ServerForUpdate')
    @patch('azure.cli.command_modules.mysql.custom.models.Server')
    @patch('azure.cli.command_modules.mysql.custom.models.MySQLServerSku')
    @patch('azure.cli.command_modules.mysql.custom.models.Backup')
    @patch('azure.cli.command_modules.mysql.custom.models.Storage')
    def test_georestore_does_not_force_source_storage_redundancy(
            self, storage_cls, backup_cls, sku_cls, server_cls, server_update_cls, is_valid_resource_id,
            parse_resource_id, get_mgmt_client_by_sub, get_list_skus_info, validate_server_name,
            get_identity_and_data_encryption, determine_iops, provision_network_resource, resolve_poller, sdk_no_wait):
        cmd = SimpleNamespace(cli_ctx=SimpleNamespace())
        client = MagicMock()

        source_server = SimpleNamespace(
            location='uksouth',
            sku=SimpleNamespace(tier='GeneralPurpose', name='Standard_D2ds_v4'),
            storage=SimpleNamespace(
                storage_size_gb=32,
                auto_grow='Enabled',
                iops=360,
                auto_io_scaling='Disabled',
                log_on_disk='Enabled',
                storage_redundancy='ZoneRedundant'),
            backup=SimpleNamespace(backup_retention_days=7, geo_redundant_backup='Enabled'),
            network=SimpleNamespace(public_network_access='Enabled'))

        restored_server = SimpleNamespace(network=SimpleNamespace(public_network_access='Enabled'))

        is_valid_resource_id.return_value = True
        parse_resource_id.return_value = {'subscription': 'sub-id', 'resource_group': 'src-rg', 'name': 'src-server'}
        get_mgmt_client_by_sub.return_value = SimpleNamespace(servers=SimpleNamespace(get=MagicMock(return_value=source_server)))
        get_list_skus_info.return_value = {'sku_info': {}, 'iops_info': {}, 'geo_paired_regions': ['ukwest']}
        get_identity_and_data_encryption.return_value = (None, None)
        determine_iops.return_value = 360
        provision_network_resource.return_value = (SimpleNamespace(public_network_access='Enabled'), None, None)
        sdk_no_wait.side_effect = lambda no_wait, func, *args, **kwargs: func(*args, **kwargs)

        storage_cls.side_effect = lambda **kwargs: SimpleNamespace(**kwargs)
        backup_cls.side_effect = lambda **kwargs: SimpleNamespace(**kwargs)
        sku_cls.side_effect = lambda **kwargs: SimpleNamespace(**kwargs)
        server_cls.side_effect = lambda **kwargs: SimpleNamespace(**kwargs)
        server_update_cls.side_effect = lambda **kwargs: SimpleNamespace(**kwargs)

        client.begin_create.return_value = MagicMock()
        client.get.return_value = restored_server
        client.begin_update.return_value = SimpleNamespace(name='updated')

        flexible_server_georestore(
            cmd=cmd,
            client=client,
            resource_group_name='target-rg',
            server_name='target-server',
            source_server='/subscriptions/sub-id/resourceGroups/src-rg/providers/Microsoft.DBforMySQL/flexibleServers/src-server',
            location='ukwest')

        self.assertNotIn('storage_redundancy', storage_cls.call_args.kwargs)


if __name__ == '__main__':
    unittest.main()
