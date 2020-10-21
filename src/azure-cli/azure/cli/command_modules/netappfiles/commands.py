# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from ._client_factory import (
    accounts_mgmt_client_factory,
    pools_mgmt_client_factory,
    volumes_mgmt_client_factory,
    snapshots_mgmt_client_factory,
    snapshot_policies_mgmt_client_factory,
    account_backups_mgmt_client_factory,
    backups_mgmt_client_factory,
    backup_policies_mgmt_client_factory,
    vaults_mgmt_client_factory)
from ._exception_handler import netappfiles_exception_handler


def load_command_table(self, _):
    netappfiles_accounts_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._accounts_operations#AccountsOperations.{}',
        client_factory=accounts_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )

    netappfiles_pools_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._pools_operations#PoolsOperations.{}',
        client_factory=pools_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )

    netappfiles_volumes_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._volumes_operations#VolumesOperations.{}',
        client_factory=volumes_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )

    netappfiles_snapshots_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._snapshots_operations#SnapshotsOperations.{}',
        client_factory=snapshots_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )

    netappfiles_snapshot_policies_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._snapshot_policies_operations#SnapshotPoliciesOperations.{}',
        client_factory=snapshot_policies_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )

    netappfiles_account_backups_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._account_backups_operations#AccountBackupsOperations.{}',
        client_factory=account_backups_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )

    netappfiles_backups_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._backups_operations#BackupsOperations.{}',
        client_factory=backups_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )

    netappfiles_backup_policies_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._backup_policies_operations#BackupPoliciesOperations.{}',
        client_factory=backup_policies_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )

    netappfiles_vaults_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._vaults_operations#VaultsOperations.{}',
        client_factory=vaults_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )

    with self.command_group('netappfiles account', netappfiles_accounts_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.custom_command('create', 'create_account',
                         client_factory=accounts_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#NetAppAccount',
                         exception_handler=netappfiles_exception_handler)
        g.generic_update_command('update',
                                 setter_name='update',
                                 custom_func_name='patch_account',
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#NetAppAccountPatch',
                                 exception_handler=netappfiles_exception_handler)

    with self.command_group('netappfiles account ad', netappfiles_accounts_sdk) as g:
        g.generic_update_command('add',
                                 setter_name='update',
                                 custom_func_name='add_active_directory',
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#NetAppAccountPatch',
                                 exception_handler=netappfiles_exception_handler)
        g.custom_command('list', 'list_active_directories',
                         client_factory=accounts_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#NetAppAccount',
                         exception_handler=netappfiles_exception_handler)

        g.custom_command('remove', 'remove_active_directory',
                         client_factory=accounts_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#NetAppAccount',
                         exception_handler=netappfiles_exception_handler)

    with self.command_group('netappfiles account backup', netappfiles_account_backups_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')

    with self.command_group('netappfiles account backup-policy', netappfiles_backup_policies_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.custom_command('update', 'patch_backup_policy',
                         client_factory=backup_policies_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#BackupPolicyPatch',
                         exception_handler=netappfiles_exception_handler)
        g.custom_command('create', 'create_backup_policy',
                         client_factory=backup_policies_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#BackupPolicy',
                         exception_handler=netappfiles_exception_handler)

    with self.command_group('netappfiles pool', netappfiles_pools_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.custom_command('create', 'create_pool',
                         client_factory=pools_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#CapacityPool',
                         exception_handler=netappfiles_exception_handler)
        g.generic_update_command('update',
                                 setter_name='update',
                                 custom_func_name='patch_pool',
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#CapacityPoolPatch',
                                 exception_handler=netappfiles_exception_handler)

    with self.command_group('netappfiles volume', netappfiles_volumes_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.custom_command('create', 'create_volume',
                         client_factory=volumes_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#Volume',
                         exception_handler=netappfiles_exception_handler)
        g.generic_update_command('update',
                                 setter_name='update',
                                 custom_func_name='patch_volume',
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#VolumePatch',
                                 exception_handler=netappfiles_exception_handler)
        g.custom_command('revert', 'revert_snapshot',
                         client_factory=volumes_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#Volume',
                         exception_handler=netappfiles_exception_handler)
        g.command('pool-change', 'pool_change')

    with self.command_group('netappfiles volume export-policy', netappfiles_volumes_sdk) as g:
        g.generic_update_command('add',
                                 setter_name='update',
                                 custom_func_name='add_export_policy_rule',
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#VolumePatch',
                                 exception_handler=netappfiles_exception_handler)
        g.custom_command('list', 'list_export_policy_rules',
                         client_factory=volumes_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#Volume',
                         exception_handler=netappfiles_exception_handler)
        g.generic_update_command('remove',
                                 setter_name='update',
                                 custom_func_name='remove_export_policy_rule',
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#VolumePatch',
                                 exception_handler=netappfiles_exception_handler)

    with self.command_group('netappfiles volume replication', netappfiles_volumes_sdk) as g:
        g.custom_command('approve', 'authorize_replication',
                         client_factory=volumes_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#Volume',
                         exception_handler=netappfiles_exception_handler)
        g.command('suspend', 'break_replication')
        g.command('resume', 'resync_replication')
        g.command('remove', 'delete_replication')
        g.command('status', 'replication_status_method')
        g.command('re-initialize', 're_initialize_replication')

    with self.command_group('netappfiles volume backup', netappfiles_backups_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.command('update', 'update')
        g.command('create', 'create')

    with self.command_group('netappfiles snapshot', netappfiles_snapshots_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.custom_command('create', 'create_snapshot',
                         client_factory=snapshots_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#Snapshot',
                         exception_handler=netappfiles_exception_handler)

    with self.command_group('netappfiles snapshot policy', netappfiles_snapshot_policies_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.custom_command('volumes', 'list_volumes',
                         client_factory=snapshot_policies_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#SnapshotPolicy',
                         exception_handler=netappfiles_exception_handler)
        g.command('delete', 'delete')
        g.custom_command('update', 'patch_snapshot_policy',
                         client_factory=snapshot_policies_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#SnapshotPolicyPatch',
                         exception_handler=netappfiles_exception_handler)
        g.custom_command('create', 'create_snapshot_policy',
                         client_factory=snapshot_policies_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#SnapshotPolicy',
                         exception_handler=netappfiles_exception_handler)

    with self.command_group('netappfiles vault', netappfiles_vaults_sdk) as g:
        g.command('list', 'list')

    with self.command_group('netappfiles', is_preview=True) as g:
        pass
