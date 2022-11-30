# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType

from azure.cli.command_modules.netappfiles._client_factory import (
    accounts_mgmt_client_factory,
    pools_mgmt_client_factory,
    volumes_mgmt_client_factory,
    snapshots_mgmt_client_factory,
    snapshot_policies_mgmt_client_factory,
    account_backups_mgmt_client_factory,
    backups_mgmt_client_factory,
    backup_policies_mgmt_client_factory,
    vaults_mgmt_client_factory,
    subvolumes_mgmt_client_factory,
    volume_groups_mgmt_client_factory,
    netapp_resource_mgmt_client_factory)

from azure.cli.command_modules.netappfiles._exception_handler import netappfiles_exception_handler


def load_command_table(self, _):
    netappfiles_accounts_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._accounts_operations#AccountsOperations.{}',
        client_factory=accounts_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )
    load_accounts_command_groups(self, netappfiles_accounts_sdk)

    netappfiles_pools_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._pools_operations#PoolsOperations.{}',
        client_factory=pools_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )
    load_pools_command_groups(self, netappfiles_pools_sdk)

    netappfiles_volumes_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._volumes_operations#VolumesOperations.{}',
        client_factory=volumes_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )
    load_volumes_command_groups(self, netappfiles_volumes_sdk)

    netappfiles_snapshots_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._snapshots_operations#SnapshotsOperations.{}',
        client_factory=snapshots_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )
    load_snapshots_command_groups(self, netappfiles_snapshots_sdk)

    netappfiles_snapshot_policies_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._snapshot_policies_operations#SnapshotPoliciesOperations.{}',
        client_factory=snapshot_policies_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )
    load_snapshots_policies_command_groups(self, netappfiles_snapshot_policies_sdk)

    netappfiles_account_backups_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._account_backups_operations#AccountBackupsOperations.{}',
        client_factory=account_backups_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )
    load_account_backup_command_groups(self, netappfiles_account_backups_sdk)

    netappfiles_backups_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._backups_operations#BackupsOperations.{}',
        client_factory=backups_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )
    load_backups_command_groups(self, netappfiles_backups_sdk)

    netappfiles_backup_policies_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._backup_policies_operations#BackupPoliciesOperations.{}',
        client_factory=backup_policies_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )
    load_backup_policies_command_groups(self, netappfiles_backup_policies_sdk)

    netappfiles_vaults_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._vaults_operations#VaultsOperations.{}',
        client_factory=vaults_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )
    load_vaults_command_groups(self, netappfiles_vaults_sdk)

    netappfiles_subvolumes_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._subvolumes_operations#SubvolumesOperations.{}',
        client_factory=subvolumes_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )
    load_subvolumes_command_groups(self, netappfiles_subvolumes_sdk)

    netappfiles_volume_groups_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._volume_groups_operations#VolumeGroupsOperations.{}',
        client_factory=volume_groups_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )
    load_volume_groups_command_groups(self, netappfiles_volume_groups_sdk)

    netappfiles_resource_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.netapp.operations._net_app_resource_operations#NetAppResourceOperations.{}',
        client_factory=netapp_resource_mgmt_client_factory,
        exception_handler=netappfiles_exception_handler
    )
    load_net_app_resource_command_groups(self, netappfiles_resource_sdk)

    with self.command_group('netappfiles', is_preview=False):
        pass


def load_accounts_command_groups(self, netappfiles_accounts_sdk):
    with self.command_group('netappfiles account', netappfiles_accounts_sdk) as g:
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete', supports_no_wait=True)
        g.custom_command('list', 'list_accounts',
                         client_factory=accounts_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#NetAppAccountList',
                         exception_handler=netappfiles_exception_handler)
        g.custom_command('create', 'create_account',
                         client_factory=accounts_mgmt_client_factory,
                         supports_no_wait=True,
                         doc_string_source='azure.mgmt.netapp.models#NetAppAccount',
                         exception_handler=netappfiles_exception_handler)
        g.generic_update_command('update',
                                 setter_name='begin_update',
                                 supports_no_wait=True,
                                 custom_func_name='patch_account',
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#NetAppAccountPatch',
                                 exception_handler=netappfiles_exception_handler)
        g.command('renew-credentials', 'begin_renew_credentials', supports_no_wait=True, is_preview=True)
        g.wait_command('wait')

    with self.command_group('netappfiles account ad', netappfiles_accounts_sdk) as g:
        g.generic_update_command('add',
                                 setter_name='begin_update',
                                 supports_no_wait=True,
                                 custom_func_name='add_active_directory',
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#NetAppAccountPatch',
                                 exception_handler=netappfiles_exception_handler)
        g.generic_update_command('update',
                                 setter_name='begin_update',
                                 supports_no_wait=True,
                                 custom_func_name='update_active_directory',
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#NetAppAccountPatch',
                                 exception_handler=netappfiles_exception_handler)
        g.custom_command('list', 'list_active_directories',
                         client_factory=accounts_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#NetAppAccount',
                         exception_handler=netappfiles_exception_handler)
        g.custom_command('remove', 'remove_active_directory',
                         client_factory=accounts_mgmt_client_factory,
                         supports_no_wait=True,
                         doc_string_source='azure.mgmt.netapp.models#NetAppAccount',
                         exception_handler=netappfiles_exception_handler)
        g.wait_command('wait')


def load_account_backup_command_groups(self, netappfiles_account_backups_sdk):
    with self.command_group('netappfiles account backup', netappfiles_account_backups_sdk, is_preview=True) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'begin_delete', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')


def load_backup_policies_command_groups(self, netappfiles_backup_policies_sdk):
    with self.command_group('netappfiles account backup-policy', netappfiles_backup_policies_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'begin_delete', supports_no_wait=True)
        g.generic_update_command('update',
                                 setter_name='begin_update',
                                 custom_func_name='patch_backup_policy',
                                 supports_no_wait=True,
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#BackupPolicyPatch',
                                 exception_handler=netappfiles_exception_handler)
        g.custom_command('create', 'create_backup_policy',
                         client_factory=backup_policies_mgmt_client_factory,
                         supports_no_wait=True,
                         doc_string_source='azure.mgmt.netapp.models#BackupPolicy',
                         exception_handler=netappfiles_exception_handler)
        g.wait_command('wait')


def load_pools_command_groups(self, netappfiles_pools_sdk):
    with self.command_group('netappfiles pool', netappfiles_pools_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'begin_delete', supports_no_wait=True)
        g.custom_command('create', 'create_pool',
                         client_factory=pools_mgmt_client_factory,
                         supports_no_wait=True,
                         doc_string_source='azure.mgmt.netapp.models#CapacityPool',
                         exception_handler=netappfiles_exception_handler)
        g.generic_update_command('update',
                                 setter_name='begin_update',
                                 custom_func_name='patch_pool',
                                 supports_no_wait=True,
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#CapacityPoolPatch',
                                 exception_handler=netappfiles_exception_handler)
        g.wait_command('wait')


def load_volumes_command_groups(self, netappfiles_volumes_sdk):
    with self.command_group('netappfiles volume', netappfiles_volumes_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'begin_delete', supports_no_wait=True)
        g.custom_command('create', 'create_volume',
                         client_factory=volumes_mgmt_client_factory,
                         supports_no_wait=True,
                         doc_string_source='azure.mgmt.netapp.models#Volume',
                         exception_handler=netappfiles_exception_handler)
        g.generic_update_command('update',
                                 setter_name='begin_update',
                                 custom_func_name='patch_volume',
                                 supports_no_wait=True,
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#VolumePatch',
                                 exception_handler=netappfiles_exception_handler)
        g.custom_command('revert', 'volume_revert',
                         client_factory=volumes_mgmt_client_factory,
                         supports_no_wait=True,
                         doc_string_source='azure.mgmt.netapp.models#Volume',
                         exception_handler=netappfiles_exception_handler)
        g.custom_command('pool-change', 'pool_change',
                         client_factory=volumes_mgmt_client_factory,
                         supports_no_wait=True,
                         doc_string_source='azure.mgmt.netapp.models#Volume',
                         exception_handler=netappfiles_exception_handler)
        g.command('reset-cifs-pw', 'begin_reset_cifs_password', supports_no_wait=True)
        g.command('relocate', 'begin_relocate', supports_no_wait=True)
        g.command('finalize-relocation', 'begin_finalize_relocation', supports_no_wait=True)
        g.command('revert-relocation', 'begin_revert_relocation', supports_no_wait=True, confirmation=True)
        g.wait_command('wait')

    with self.command_group('netappfiles volume export-policy', netappfiles_volumes_sdk) as g:
        g.generic_update_command('add',
                                 setter_name='begin_update',
                                 custom_func_name='add_export_policy_rule',
                                 supports_no_wait=True,
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#VolumePatch',
                                 exception_handler=netappfiles_exception_handler)
        g.custom_command('list', 'list_export_policy_rules',
                         client_factory=volumes_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#Volume',
                         exception_handler=netappfiles_exception_handler)
        g.generic_update_command('remove',
                                 supports_no_wait=True,
                                 setter_name='begin_update',
                                 custom_func_name='remove_export_policy_rule',
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#VolumePatch',
                                 exception_handler=netappfiles_exception_handler)
        g.wait_command('wait')

    with self.command_group('netappfiles volume replication', netappfiles_volumes_sdk) as g:
        g.custom_command('approve', 'authorize_replication',
                         client_factory=volumes_mgmt_client_factory,
                         supports_no_wait=True,
                         doc_string_source='azure.mgmt.netapp.models#Volume',
                         exception_handler=netappfiles_exception_handler)
        g.custom_command('suspend', 'break_replication',
                         client_factory=volumes_mgmt_client_factory,
                         supports_no_wait=True,
                         doc_string_source='azure.mgmt.netapp.models#Volume',
                         exception_handler=netappfiles_exception_handler)
        g.command('resume', 'begin_resync_replication', supports_no_wait=True)
        g.command('remove', 'begin_delete_replication', supports_no_wait=True)
        g.command('status', 'replication_status')
        g.command('re-initialize', 'begin_re_initialize_replication', supports_no_wait=True)
        g.command('list', 'list_replications')
        g.wait_command('wait')


def load_backups_command_groups(self, netappfiles_backups_sdk):
    with self.command_group('netappfiles volume backup', netappfiles_backups_sdk, is_preview=True) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'begin_delete', supports_no_wait=True)
        g.command('status', 'get_status')
        g.command('restore-status', 'get_volume_restore_status')
        g.generic_update_command('update',
                                 supports_no_wait=True,
                                 setter_name='begin_update',
                                 custom_func_name='update_backup',
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#BackupPatch',
                                 exception_handler=netappfiles_exception_handler)
        g.custom_command('create', 'create_backup',
                         client_factory=backups_mgmt_client_factory,
                         supports_no_wait=True,
                         doc_string_source='azure.mgmt.netapp.models#Backup',
                         exception_handler=netappfiles_exception_handler)
        g.wait_command('wait')


def load_snapshots_command_groups(self, netappfiles_snapshots_sdk):
    with self.command_group('netappfiles snapshot', netappfiles_snapshots_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'begin_delete', supports_no_wait=True)
        g.custom_command('create', 'create_snapshot',
                         client_factory=snapshots_mgmt_client_factory,
                         supports_no_wait=True,
                         doc_string_source='azure.mgmt.netapp.models#Snapshot',
                         exception_handler=netappfiles_exception_handler)
        g.command('update', 'begin_update', supports_no_wait=True)
        g.custom_command('restore-files', 'snapshot_restore_files',
                         client_factory=snapshots_mgmt_client_factory,
                         supports_no_wait=True,
                         doc_string_source='azure.mgmt.netapp.models#SnapshotRestoreFiles',
                         exception_handler=netappfiles_exception_handler)
        g.wait_command('wait')


def load_snapshots_policies_command_groups(self, netappfiles_snapshot_policies_sdk):
    with self.command_group('netappfiles snapshot policy', netappfiles_snapshot_policies_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('volumes', 'list_volumes')
        g.command('delete', 'begin_delete', supports_no_wait=True)
        g.custom_command('update', 'patch_snapshot_policy',
                         client_factory=snapshot_policies_mgmt_client_factory,
                         supports_no_wait=True,
                         doc_string_source='azure.mgmt.netapp.models#SnapshotPolicyPatch',
                         exception_handler=netappfiles_exception_handler)
        g.custom_command('create', 'create_snapshot_policy',
                         client_factory=snapshot_policies_mgmt_client_factory,
                         doc_string_source='azure.mgmt.netapp.models#SnapshotPolicy',
                         exception_handler=netappfiles_exception_handler)
        g.wait_command('wait')


def load_vaults_command_groups(self, netappfiles_vaults_sdk):
    with self.command_group('netappfiles vault', netappfiles_vaults_sdk) as g:
        g.command('list', 'list')


def load_subvolumes_command_groups(self, netappfiles_subvolumes_sdk):
    with self.command_group('netappfiles subvolume', netappfiles_subvolumes_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list_by_volume')
        g.custom_command('create', 'create_subvolume',
                         client_factory=subvolumes_mgmt_client_factory,
                         supports_no_wait=True,
                         doc_string_source='azure.mgmt.netapp.models#SubvolumeInfo',
                         exception_handler=netappfiles_exception_handler)
        g.generic_update_command('update',
                                 setter_name='begin_update',
                                 custom_func_name='patch_subvolume',
                                 supports_no_wait=True,
                                 setter_arg_name='body',
                                 doc_string_source='azure.mgmt.netapp.models#SubvolumePatchRequest',
                                 exception_handler=netappfiles_exception_handler)
        g.command('delete', 'begin_delete', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('netappfiles subvolume metadata', netappfiles_subvolumes_sdk) as g:
        g.show_command('show', 'begin_get_metadata')


def load_volume_groups_command_groups(self, netappfiles_volume_groups_sdk):
    with self.command_group('netappfiles volume-group', netappfiles_volume_groups_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list_by_net_app_account')
        g.custom_command('create', 'create_volume_group',
                         client_factory=volume_groups_mgmt_client_factory,
                         supports_no_wait=True,
                         doc_string_source='azure.mgmt.netapp.models#VolumeGroupDetails',
                         exception_handler=netappfiles_exception_handler)
        g.command('delete', 'begin_delete', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')


def load_net_app_resource_command_groups(self, netappfiles_resource_sdk):
    with self.command_group('netappfiles resource', netappfiles_resource_sdk) as g:
        g.command('query-region-info', 'query_region_info', supports_no_wait=True)
