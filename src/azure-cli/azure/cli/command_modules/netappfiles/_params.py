# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, disable=too-many-statements
from azure.cli.core.commands.parameters import tags_type, resource_group_name_type, get_enum_type, get_three_state_flag
from azure.mgmt.netapp.models._net_app_management_client_enums import EncryptionKeySource, SmbAccessBasedEnumeration, SmbNonBrowsable, ManagedServiceIdentityType, SecurityStyle
from knack.arguments import CLIArgumentType


def load_arguments(self, _):
    account_name_type = CLIArgumentType(options_list=['--account-name', '-a'], id_part='name', help='Name of the ANF account.')
    pool_name_type = CLIArgumentType(options_list=['--pool-name', '-p'], id_part='child_name_1', help='Name of the ANF pool.')
    volume_name_type = CLIArgumentType(options_list=['--volume-name', '-v'], id_part='child_name_2', help='Name of the ANF volume.')

    with self.argument_context('netappfiles') as c:
        c.argument('resource_group', resource_group_name_type)
        c.argument('tags', arg_type=tags_type)
        c.argument('protocol_types', nargs="+")
        c.argument('account_name', account_name_type)
        c.argument('pool_name', pool_name_type)
        c.argument('volume_name', volume_name_type)
        c.argument('snapshot_name', options_list=['--snapshot-name', '-s'], help='The name of the ANF snapshot')
        c.argument('tag', tags_type)
        c.argument('service_level', options_list=['--service-level'], arg_type=get_enum_type(['Standard', 'Premium', 'Ultra']), help='Service level')
        c.argument('enabled', options_list=['--enabled', '-e'], arg_type=get_three_state_flag(), id_part=None)

    with self.argument_context('netappfiles account') as c:
        c.argument('account_name', account_name_type, options_list=['--name', '--account-name', '-n', '-a'])

    with self.argument_context('netappfiles account', arg_group='Encryption') as c:
        c.argument('key_source', arg_type=get_enum_type(EncryptionKeySource), options_list=['--key-source'], help='The encryption keySource (provider).', is_preview=True)
        c.argument('key_vault_uri', options_list=['--key-vault-uri', '-v'], help='The Uri of KeyVault.', is_preview=True)
        c.argument('key_name', options_list=['--key-name'], help='The name of KeyVault key.', is_preview=True)
        c.argument('key_vault_resource_id', options_list=['--keyvault-resource-id'], help='The resource ID of KeyVault.', is_preview=True)
        c.argument('user_assigned_identity', arg_group='Identity', options_list=['--user-assigned-identity', '-u'], help='The ARM resource identifier of the user assigned identity used to authenticate with key vault. Applicable if identity.type has ''UserAssigned''. It should match key of identity.userAssignedIdentities.', is_preview=True)
        c.argument('encryption', help='This argument will be deprecated, please use --key-source instead', deprecate_info=c.deprecate(hide=False, redirect='--key-source'))
        c.argument('identity_type', arg_type=get_enum_type(ManagedServiceIdentityType), arg_group='Identity', help='The identity type.')

    with self.argument_context('netappfiles account list') as c:
        c.argument('account_name', help='The name of the ANF account', id_part=None)

    with self.argument_context('netappfiles account ad') as c:
        c.argument('backup_operators', nargs="+")
        c.argument('security_operators', nargs="+")
        c.argument('administrators', nargs="+")
        c.argument('allow_local_ldap_users', arg_type=get_three_state_flag())
        c.argument('encrypt_dc_conn', options_list=['--encrypt-dc-conn'], arg_type=get_three_state_flag())
        c.argument('ldap_signing', arg_type=get_three_state_flag())
        c.argument('aes_encryption', arg_type=get_three_state_flag())
        c.argument('preferred_servers_for_ldap_client', nargs="+", options_list=['--preferred-servers-for-ldap-client', '-p'], help='Comma separated list of IPv4 addresses of preferred servers for LDAP client. At most two comma separated IPv4 addresses can be passed.')

    with self.argument_context('netappfiles account ad list') as c:
        c.argument('account_name', help='The name of the ANF account', id_part=None)

    with self.argument_context('netappfiles account backup-policy') as c:
        c.argument('account_name', account_name_type)
        c.argument('backup_policy_name', options_list=['--backup-policy-name', '-b'], help='The name of the backup policy', id_part='child_name_1')
        c.argument('daily_backups', options_list=['--daily-backups', '-d'], help='Daily backups count to keep')
        c.argument('weekly_backups', options_list=['--weekly-backups', '-w'], help='Weekly backups count to keep')
        c.argument('monthly_backups', options_list=['--monthly-backups', '-m'], help='Monthly backups count to keep')

    with self.argument_context('netappfiles account backup-policy list') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('backup_policy_name', options_list=['--backup-policy-name', '-b'], help='The name of the backup policy')

    with self.argument_context('netappfiles account backup') as c:
        c.argument('account_name', account_name_type, id_part=None)

    load_pool_arguments(self, account_name_type, pool_name_type)
    load_volume_arguments(self, account_name_type, pool_name_type, volume_name_type)
    load_snapshot_arguments(self, account_name_type, pool_name_type, volume_name_type)
    load_vault_arguments(self, account_name_type)
    load_subvolume_arguments(self, account_name_type, pool_name_type, volume_name_type)
    load_volume_groups_arguments(self, account_name_type, pool_name_type)
    load_volume_quota_rules_arguments(self, account_name_type, pool_name_type, volume_name_type)


def load_pool_arguments(self, account_name_type, pool_name_type):
    with self.argument_context('netappfiles pool') as c:
        c.argument('account_name', id_part='name')
        c.argument('pool_name', pool_name_type, options_list=['--pool-name', '-p', '--name', '-n'])
        c.argument('cool_access', arg_type=get_three_state_flag())

    with self.argument_context('netappfiles pool list') as c:
        c.argument('account_name', account_name_type, id_part=None)


def load_volume_arguments(self, account_name_type, pool_name_type, volume_name_type):
    with self.argument_context('netappfiles volume') as c:
        c.argument('account_name', id_part='name')
        c.argument('pool_name', pool_name_type)
        c.argument('volume_name', volume_name_type, options_list=['--volume-name', '-v', '--name', '-n'])
        c.argument('backup_enabled', arg_type=get_three_state_flag())
        c.argument('policy_enforced', arg_type=get_three_state_flag())
        c.argument('kerberos_enabled', arg_type=get_three_state_flag())
        c.argument('smb_encryption', arg_type=get_three_state_flag())
        c.argument('smb_continuously_avl', arg_type=get_three_state_flag())
        c.argument('unix_read_only', arg_type=get_three_state_flag())
        c.argument('unix_read_write', arg_type=get_three_state_flag())
        c.argument('cifs', arg_type=get_three_state_flag())
        c.argument('ldap_enabled', arg_type=get_three_state_flag())
        c.argument('cool_access', arg_type=get_three_state_flag())
        c.argument('is_def_quota_enabled', arg_type=get_three_state_flag())
        c.argument('has_root_access', help="Vol Has root access to volume", arg_type=get_three_state_flag())
        c.argument('snapshot_dir_visible', arg_type=get_three_state_flag())
        c.argument('security_style', arg_type=get_enum_type(SecurityStyle), help='The security style of volume, default unix, defaults to ntfs for dual protocol or CIFS protocol')

    with self.argument_context('netappfiles volume create') as c:
        c.argument('zones', nargs="+")
        c.argument('smb_access_based_enumeration', arg_type=get_enum_type(SmbAccessBasedEnumeration), options_list=['--smb-access'], help='Enables access based enumeration share property for SMB Shares. Only applicable for SMB/DualProtocol volume')
        c.argument('smb_non_browsable', arg_type=get_enum_type(SmbNonBrowsable), options_list=['--smb-browsable'], help='Enables non browsable property for SMB Shares. Only applicable for SMB/DualProtocol volume')
        c.argument('delete_base_snapshot', arg_type=get_three_state_flag(), help='If enabled (true) the snapshot the volume was created from will be automatically deleted after the volume create operation has finished.  Defaults to false')
        c.argument('is_large_volume', arg_type=get_three_state_flag(), help='Specifies whether volume is a Large Volume or Regular Volume.')

    with self.argument_context('netappfiles volume delete') as c:
        c.argument('force_delete', arg_type=get_three_state_flag())

    with self.argument_context('netappfiles volume list') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('pool_name', options_list=['--pool-name', '-p'], help='Name of the ANF pool.', id_part=None)

    with self.argument_context('netappfiles volume revert') as c:
        c.argument('account_name', id_part=None)
        c.argument('pool_name', pool_name_type, id_part=None)
        c.argument('volume_name', volume_name_type, options_list=['--volume-name', '-v', '--name', '-n'], id_part=None)
        c.argument('snapshot_id', options_list=['--snapshot-id', '-s'], help='Resource id of the snapshot', id_part=None)

    with self.argument_context('netappfiles volume break-file-locks') as c:
        c.argument('client_ip', options_list=['--client-ip', '-i'], help='To clear file locks on a volume for a particular client', id_part=None)

    with self.argument_context('netappfiles volume pool-change') as c:
        c.argument('new_pool_resource_id', options_list=['--new-pool-resource-id', '-d'], help='Resource id of the new pool')

    with self.argument_context('netappfiles volume export-policy list') as c:
        c.argument('account_name', id_part=None)
        c.argument('pool_name', pool_name_type, id_part=None)
        c.argument('volume_name', volume_name_type, options_list=['--volume-name', '-v', '--name', '-n'], id_part=None)

    with self.argument_context('netappfiles volume replication approve') as c:
        c.argument('account_name', id_part=None)
        c.argument('pool_name', pool_name_type, id_part=None)
        c.argument('volume_name', volume_name_type, options_list=['--volume-name', '-v', '--name', '-n'], id_part=None)
        c.argument('remote_volume_resource_id', options_list=['--remote-volume-resource-id', '-d'], help='The id of the destination replication volume')

    with self.argument_context('netappfiles volume replication list') as c:
        c.argument('account_name', id_part=None)
        c.argument('pool_name', pool_name_type, id_part=None)
        c.argument('volume_name', volume_name_type, options_list=['--volume-name', '-v', '--name', '-n'], id_part=None)

    with self.argument_context('netappfiles volume replication suspend') as c:
        c.argument('force_break_replication', options_list=['--force', '--force-break-replication', '-f'], arg_type=get_three_state_flag())

    with self.argument_context('netappfiles volume export-policy add') as c:
        c.argument('unix_read_only', help="Indication of read only access", arg_type=get_three_state_flag())
        c.argument('unix_read_write', help="Indication of read and write access", arg_type=get_three_state_flag())
        c.argument('cifs', help="Indication that CIFS protocol is allowed", arg_type=get_three_state_flag())
        c.argument('nfsv3', help="Indication that NFSv3 protocol is allowed", arg_type=get_three_state_flag())
        c.argument('nfsv41', help="Indication that NFSv4.1 protocol is allowed", arg_type=get_three_state_flag())

    with self.argument_context('netappfiles volume backup') as c:
        c.argument('backup_name', options_list=['--backup-name', '-b'], id_part='child_name_3')
        c.argument('use_existing_snapshot', arg_type=get_three_state_flag())

    with self.argument_context('netappfiles volume backup list') as c:
        c.argument('account_name', id_part=None)
        c.argument('pool_name', pool_name_type, id_part=None)
        c.argument('backup_name', options_list=['--backup-name', '-b'], id_part=None)


def load_snapshot_arguments(self, account_name_type, pool_name_type, volume_name_type):
    with self.argument_context('netappfiles snapshot') as c:
        c.argument('account_name', account_name_type)
        c.argument('pool_name', pool_name_type)
        c.argument('volume_name', volume_name_type)
        c.argument('snapshot_name', id_part='child_name_3', options_list=['--name', '--snapshot-name', '-n', '-s'], help='The name of the ANF snapshot')
        c.argument('file_paths', nargs="+")

    with self.argument_context('netappfiles snapshot list') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('volume_name', options_list=['--volume-name', '-v'], help='The name of the ANF volume', id_part=None)

    with self.argument_context('netappfiles snapshot policy') as c:
        c.argument('account_name', account_name_type)
        c.argument('snapshot_policy_name', help='The name of the snapshot policy', id_part='child_name_1')
        c.argument('hourly_snapshots', options_list=['--hourly-snapshots', '-u'], help='The amount of hourly snapshots to keep')
        c.argument('daily_snapshots', options_list=['--daily-snapshots', '-d'], help='The amount of daily snapshots to keep')
        c.argument('weekly_snapshots', options_list=['--weekly-snapshots', '-w'], help='The amount of weekly snapshots to keep')
        c.argument('monthly_snapshots', options_list=['--monthly-snapshots', '-m'], help='The amount of monthly snapshots to keep')

    with self.argument_context('netappfiles snapshot policy list') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('snapshot_policy_name', options_list=['--snapshot-policy-name', '--name', '-n'], help='The name of the snapshot policy')


def load_vault_arguments(self, account_name_type):
    with self.argument_context('netappfiles vault list') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('loc', deprecate_info=c.deprecate(hide=False))


def load_subvolume_arguments(self, account_name_type, pool_name_type, volume_name_type):
    with self.argument_context('netappfiles subvolume') as c:
        c.argument('account_name', account_name_type)
        c.argument('pool_name', pool_name_type)
        c.argument('volume_name', volume_name_type)
        c.argument('subvolume_name', id_part="child_name_3")

    with self.argument_context('netappfiles subvolume list') as c:
        c.argument('account_name', id_part=None)
        c.argument('pool_name', id_part=None)
        c.argument('volume_name', id_part=None)
        c.argument('subvolume_name', id_part=None)


def load_volume_quota_rules_arguments(self, account_name_type, pool_name_type, volume_name_type):
    with self.argument_context('netappfiles volume quota-rule') as c:
        c.argument('account_name', account_name_type)
        c.argument('pool_name', pool_name_type)
        c.argument('volume_name', volume_name_type)
        c.argument('volume_quota_rule_name', options_list=['--quota-rule-name'], help='The name of the quota rule')
        c.argument('quota_size', options_list=['--quota-size'], help='Size of quota')

    with self.argument_context('netappfiles volume quota-rule list') as c:
        c.argument('account_name', id_part=None)
        c.argument('pool_name', pool_name_type, id_part=None)
        c.argument('volume_name', volume_name_type, options_list=['--volume-name', '-v', '--name', '-n'], id_part=None)


def load_volume_groups_arguments(self, account_name_type, pool_name_type):
    with self.argument_context('netappfiles volume-group', id_part=None) as c:
        c.argument('account_name', account_name_type)
        c.argument('pool_name', pool_name_type)
        c.argument('volume_group_name', options_list=['--volume-group-name', '--group-name'], id_part='child_name_1',
                   help='The name of the ANF volume group')
        c.argument('gp_rules', options_list=['--gp-rules', '--global-placement-rules'], nargs="+",
                   help='Application specific identifier of deployment rules for the volume group. Space-separated string in `key=value` format')
        c.argument('system_role', arg_type=get_enum_type(['PRIMARY', 'HA', 'DR']))
        c.argument('add_snapshot_capacity', type=int, default=50,
                   help="Additional memory to store snapshots, must be specified as % of RAM (range 0-200). "
                        "This is used to auto compute storage size")
        c.argument('memory', type=int, default=100,
                   help="SAP HANA memory in GiB (max 12000 GiB), used to auto compute storage size and throughput")
        c.argument('start_host_id', type=int, default=1,
                   help="Starting SAP HANA Host ID. Host ID 1 indicates Master Host. "
                        "Shared, Data Backup and Log Backup volumes are only provisioned for Master Host "
                        "i.e. `HostID == 1`")
        c.argument('number_of_hots', type=int, default=1,
                   help="Total Number of SAP HANA host in this deployment (currently max 3 nodes can be configured)")
        c.argument('data_size', type=int, help="Capacity (in GiB) for data volumes. If not provided size will automatically be calculated")
        c.argument('data_throughput', type=int, help="Throughput in MiB/s for data volumes. If not provided size will automatically be calculated")
        c.argument('log_size', type=int, help="Capacity (in GiB) for log volumes. If not provided size will automatically be calculated")
        c.argument('log_throughput', type=int, help="Throughput in MiB/s for log volumes. If not provided size will automatically be calculated")
        c.argument('shared_size', type=int, help="Capacity (in GiB) for shared volume. If not provided size will automatically be calculated")
        c.argument('shared_throughput', type=int, help="Throughput in MiB/s for shared volume. If not provided size will automatically be calculated")
        c.argument('data_backup_size', type=int, help="Capacity (in GiB) for data backup volumes. If not provided size will automatically be calculated")
        c.argument('data_backup_throughput', type=int, help="Throughput in MiB/s for data backup volumes. If not provided size will automatically be calculated")
        c.argument('log_backup_size', type=int, help="Capacity (in GiB) for log backup volumes. If not provided size will automatically be calculated")
        c.argument('log_backup_throughput', type=int, help="Throughput in MiB/s for log backup volumes. If not provided size will automatically be calculated")
        c.argument('smb_access_based_enumeration', arg_type=get_enum_type(SmbAccessBasedEnumeration), options_list=['--smb-access'], help='Enables access based enumeration share property for SMB Shares. Only applicable for SMB/DualProtocol volume')
        c.argument('smb_non_browsable', arg_type=get_enum_type(SmbNonBrowsable), options_list=['--smb-browsable'], help='Enables non browsable property for SMB Shares. Only applicable for SMB/DualProtocol volume')

    with self.argument_context('netappfiles volume-group list') as c:
        c.argument('account_name', id_part=None)
        c.argument('pool_name', id_part=None)
        c.argument('volume_name', id_part=None)
        c.argument('volume_group_name', id_part=None)
