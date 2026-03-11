# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import tags_type, get_location_type, get_enum_type, file_type, resource_group_name_type, get_three_state_flag
from azure.cli.command_modules.mysql.action import AddArgs
from azure.cli.command_modules.mysql.random.generate import generate_username
from azure.cli.command_modules.mysql._validators import public_access_validator, maintenance_window_validator, ip_address_validator, \
    firewall_rule_name_validator, validate_identity, validate_byok_identity, validate_identities, validate_action_name, validate_branch
from azure.cli.core.local_context import LocalContextAttribute, LocalContextAction
from ._util import get_current_time
from argcomplete.completers import FilesCompleter


def load_arguments(self, _):    # pylint: disable=too-many-statements, too-many-locals
    server_name_arg_type = CLIArgumentType(
        metavar='NAME',
        options_list=['--name', '-n'],
        id_part='name',
        help="Name of the server. The name can contain only lowercase letters, numbers, and the hyphen (-) character. Minimum 3 characters and maximum 63 characters.",
        local_context_attribute=LocalContextAttribute(
            name='server_name',
            actions=[LocalContextAction.SET, LocalContextAction.GET],
            scopes=['mysql flexible-server']))

    migration_id_arg_type = CLIArgumentType(
        metavar='NAME',
        help="ID of the migration.",
        local_context_attribute=LocalContextAttribute(
            name='migration_id',
            actions=[LocalContextAction.SET, LocalContextAction.GET],
            scopes=['mysql flexible-server']))

    administrator_login_arg_type = CLIArgumentType(
        options_list=['--admin-user', '-u'],
        arg_group='Authentication',
        help='Administrator username for the server. Once set, it cannot be changed. ',
        local_context_attribute=LocalContextAttribute(
            name='administrator_login',
            actions=[LocalContextAction.GET, LocalContextAction.SET],
            scopes=['mysql flexible-server']))

    administrator_login_password_arg_type = CLIArgumentType(
        options_list=['--admin-password', '-p'],
        help='The password of the administrator. Minimum 8 characters and maximum 128 characters. '
        'Password must contain characters from three of the following categories: '
        'English uppercase letters, English lowercase letters, numbers, and non-alphanumeric characters.',
        arg_group='Authentication'
    )

    database_name_arg_type = CLIArgumentType(
        metavar='NAME',
        options_list=['--database-name', '-d'],
        id_part='child_name_1',
        help='The name of the database to be created when provisioning the database server',
        local_context_attribute=LocalContextAttribute(
            name='database_name',
            actions=[LocalContextAction.GET, LocalContextAction.SET],
            scopes=['mysql flexible-server']))

    database_port_arg_type = CLIArgumentType(
        type=int,
        options_list=['--database-port'],
        help='The port of the database. Default value is 3306'
    )

    tier_arg_type = CLIArgumentType(
        options_list=['--tier'],
        help='Compute tier of the server. Accepted values: Burstable, GeneralPurpose, MemoryOptimized '
    )

    sku_name_arg_type = CLIArgumentType(
        options_list=['--sku-name'],
        help='The name of the compute SKU. Follows the convention Standard_{VM name}. Examples: Standard_B1ms'
    )

    storage_gb_arg_type = CLIArgumentType(
        type=int,
        options_list=['--storage-size'],
        help='The storage capacity of the server. Minimum is 32 GiB and max is 16 TiB.'
    )

    mysql_backup_retention_arg_type = CLIArgumentType(
        type=int,
        options_list=['--backup-retention'],
        help='The number of days a backup is retained. Range of 1 to 35 days. Default is 7 days.',
    )

    version_arg_type = CLIArgumentType(
        options_list=['--version'],
        help='Server major version.'
    )

    iops_arg_type = CLIArgumentType(
        type=int,
        options_list=['--iops'],
        help='Number of IOPS to be allocated for this server. You will get certain amount of free IOPS based '
        'on compute and storage provisioned. The default value for IOPS is free IOPS. '
        'To learn more about IOPS based on compute and storage, refer to IOPS in Azure Database for MySQL Flexible Server'
    )

    auto_grow_arg_type = CLIArgumentType(
        arg_type=get_enum_type(['Enabled', 'Disabled']),
        options_list=['--storage-auto-grow'],
        help='Enable or disable autogrow of the storage. Default value is Enabled.'
    )

    auto_scale_iops_arg_type = CLIArgumentType(
        arg_type=get_enum_type(['Enabled', 'Disabled']),
        options_list=['--auto-scale-iops'],
        help='Enable or disable the auto scale iops. Default value is Enabled.'
    )

    accelerated_logs_arg_type = CLIArgumentType(
        arg_type=get_enum_type(['Enabled', 'Disabled']),
        options_list=['--accelerated-logs'],
        help='Enable or disable accelerated logs. Only support for Business Critical tier. Default value is Enabled.'
    )

    faster_restore_arg_type = CLIArgumentType(
        arg_type=get_enum_type(['Enabled', 'Disabled']),
        options_list=['--faster-restore'],
        help='Enable or disable Auto scale IOPS configuration for both the source and the newly restored server to enable faster restore.'
    )

    faster_provisioning_arg_type = CLIArgumentType(
        arg_type=get_enum_type(['Enabled', 'Disabled']),
        options_list=['--faster-provisioning'],
        help='Enable or disable Auto scale IOPS configuration for both the source and the newly provisioned replica server to enable faster provisioning.'
    )

    storage_redundancy_arg_type = CLIArgumentType(
        arg_type=get_enum_type(['LocalRedundancy', 'ZoneRedundancy']),
        options_list=['--storage-redundancy'],
        help='Enable local redundancy or zone redundancy. Zone redundancy only supports Business Critical tier.'
    )

    maintenance_policy_patch_strategy_arg_type = CLIArgumentType(
        arg_type=get_enum_type(['Regular', 'VirtualCanary']),
        options_list=['--maintenance-policy-patch-strategy', '--patch-strategy'],
        help='The patch strategy of maintenance policy. Accepted values: Regular, VirtualCanary. Default value is Regular.'
    )

    yes_arg_type = CLIArgumentType(
        options_list=['--yes', '-y'],
        action='store_true',
        help='Do not prompt for confirmation.'
    )

    vnet_arg_type = CLIArgumentType(
        options_list=['--vnet'],
        help='Name or ID of a new or existing virtual network. '
             'This parameter only applies if you are creating cross region replica server with private access. '
             'For in-region read replica with private access, source server settings are carried over and this parameter is ignored. '
             'If you want to use a vnet from different resource group or subscription, '
             'please provide a resource ID. The name must be between 2 to 64 characters. '
             'The name must begin with a letter or number, end with a letter, number or underscore, '
             'and may contain only letters, numbers, underscores, periods, or hyphens.'
    )

    vnet_address_prefix_arg_type = CLIArgumentType(
        options_list=['--address-prefixes'],
        help='The IP address prefix to use when creating a new virtual network in CIDR format. '
             'Default value is 10.0.0.0/16.'
    )

    subnet_arg_type = CLIArgumentType(
        options_list=['--subnet'],
        help='Name or resource ID of a new or existing subnet. '
             'This parameter only applies if you are creating cross region replica server with private access. '
             'For in-region read replica with private access, source server settings are carried over and this parameter is ignored. '
             'If you want to use a subnet from different resource group or subscription, please provide resource ID instead of name. '
             'Please note that the subnet will be delegated to flexibleServers. '
             'After delegation, this subnet cannot be used for any other type of Azure resources.'
    )

    subnet_address_prefix_arg_type = CLIArgumentType(
        options_list=['--subnet-prefixes'],
        help='The subnet IP address prefix to use when creating a new subnet in CIDR format. Default value is 10.0.0.0/24.'
    )

    zone_arg_type = CLIArgumentType(
        options_list=['--zone', '-z'],
        help='Availability zone into which to provision the resource.'
    )

    public_access_update_arg_type = CLIArgumentType(
        options_list=['--public-access'],
        arg_type=get_enum_type(['Enabled', 'Disabled']),
        help='Enable or disable the public access on a server.'
    )

    public_access_create_arg_type = CLIArgumentType(
        options_list=['--public-access'],
        help='Determines the public access. Enter single or range of IP addresses to be included in the allowed list of IPs. '
             'IP address ranges must be dash-separated and not contain any spaces. '
             'Specifying 0.0.0.0 allows public access from any resources deployed within Azure to access your server. '
             'Setting it to "None" sets the server in public access mode but does not create a firewall rule. ',
        validator=public_access_validator
    )

    standby_availability_zone_arg_type = CLIArgumentType(
        options_list=['--standby-zone'],
        help="The availability zone information of the standby server when high availability is enabled."
    )

    high_availability_arg_type = CLIArgumentType(
        arg_type=get_enum_type(['ZoneRedundant', 'SameZone', 'Disabled']),
        options_list=['--high-availability'],
        help='Enable (ZoneRedundant or SameZone) or disable high availability feature.'
    )

    mysql_version_upgrade_arg_type = CLIArgumentType(
        arg_type=get_enum_type(['8', '8.4']),
        options_list=['--version', '-v'],
        help='Server major version.'
    )

    private_dns_zone_arguments_arg_type = CLIArgumentType(
        options_list=['--private-dns-zone'],
        help='This parameter only applies if you are creating cross region replica server with private access. '
             'For in-region read replica with private access, source server settings are carried over and this parameter is ignored. '
             'The name or id of new or existing private dns zone. '
             'You can use the private dns zone from same resource group, different resource group, or different subscription. '
             'If you want to use a zone from different resource group or subscription, please provide resource Id. '
             'CLI creates a new private dns zone within the same resource group as virtual network if not provided by users.'
    )

    restore_point_in_time_arg_type = CLIArgumentType(
        options_list=['--restore-time'],
        default=get_current_time(),
        help='The point in time in UTC to restore from (ISO8601 format), e.g., 2017-04-26T02:10:00+00:00'
             'The default value is set to current time.'
    )

    maintenance_reschedule_time_arg_type = CLIArgumentType(
        options_list=['--start-time'],
        default=get_current_time(),
        help='The maintenance reschedule start time in UTC(ISO8601 format), e.g., 2017-04-26T02:10:00+00:00'
             'The default value is set to current time.'
    )

    source_server_arg_type = CLIArgumentType(
        options_list=['--source-server'],
        help='The name or resource ID of the source server to restore from.'
    )

    geo_redundant_backup_arg_type = CLIArgumentType(
        options_list=['--geo-redundant-backup'],
        arg_type=get_enum_type(['Enabled', 'Disabled']),
        help='Whether or not geo redundant backup is enabled.'
    )

    identity_arg_type = CLIArgumentType(
        options_list=['--identity'],
        help='The name or resource ID of the user assigned identity for data encryption.',
        validator=validate_byok_identity
    )

    backup_identity_arg_type = CLIArgumentType(
        options_list=['--backup-identity'],
        help='The name or resource ID of the geo backup user identity for data encryption. The identity needs to be in the same region as the backup region.',
        validator=validate_byok_identity
    )

    backup_interval_arg_type = CLIArgumentType(
        type=int,
        options_list=['--backup-interval'],
        help='The interval between backups in hours. Accepted values are 24, 12 and 6. The default value is 24.'
    )

    key_arg_type = CLIArgumentType(
        options_list=['--key'],
        help='The resource ID of the primary keyvault key for data encryption.'
    )

    backup_key_arg_type = CLIArgumentType(
        options_list=['--backup-key'],
        help='The resource ID of the geo backup keyvault key for data encryption. The key needs to be in the same region as the backup region.'
    )

    disable_data_encryption_arg_type = CLIArgumentType(
        options_list=['--disable-data-encryption'],
        arg_type=get_three_state_flag(),
        help='Disable data encryption by removing key(s).'
    )

    identities_arg_type = CLIArgumentType(
        options_list=['--identity', '-n'],
        nargs='+',
        help='Space-separated names or ID\'s of identities.',
        validator=validate_identities
    )

    gtid_set_arg_type = CLIArgumentType(
        options_list=['--gtid-set'],
        help='A GTID set is a set comprising one or more single GTIDs or ranges of GTIDs. '
             'A GTID is represented as a pair of coordinates, separated by a colon character (:), as shown: source_id:transaction_id'
    )

    data_source_type_arg_type = CLIArgumentType(
        options_list=['--data-source-type'],
        arg_type=get_enum_type(['mysql_single', 'azure_blob']),
        help='Data source type. e.g., mysql_single: Azure Database for MySQL Servers. '
             'azure_blob: Source backup provided in Azure blob container.'
    )

    data_source_arg_type = CLIArgumentType(
        options_list=['--data-source'],
        help='Data source for importing to Flexible Server. Based on the data source type provide the data source as mentioned below. '
             'e.g., mysql_single: The name or resource ID of the Azure MySQL single server. '
             'azure_blob: The name or resource ID of the Azure blob container. The storage uri of the azure blob container. '
             'Example: https://{blob_name}.blob.core.windows.net/{container_name}. The storage uri should not contain the sas token. '
             'If required, sas token can be provided in "data-source-sas-token" parameter.'
    )

    data_source_backup_dir_arg_type = CLIArgumentType(
        options_list=['--data-source-backup-dir'],
        help='Relative path of the directory in which source backup is stored. '
             'By default, the backup files will be read from the root of storage. '
             'This parameter is valid for storage based data source. Example: azure_blob. '
    )

    data_source_sas_token_arg_type = CLIArgumentType(
        options_list=['--data-source-sas-token'],
        help='Sas token for accessing the data source. This parameter is valid for storage based data source. Example: azure_blob. '
    )

    mode_arg_type = CLIArgumentType(
        options_list=['--mode'],
        arg_type=get_enum_type(['Offline', 'Online']),
        help='Mode of import. Enum values: [Offline, Online]. Default is Offline. '
    )

    with self.argument_context('mysql flexible-server') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('server_name', arg_type=server_name_arg_type)

    # Advanced Threat Protection
    with self.argument_context('mysql flexible-server advanced-threat-protection-setting update') as c:
        c.argument('state',
                   options_list=['--state'],
                   required=True,
                   arg_type=get_enum_type(['Enabled', 'Disabled']),
                   help="State of server's advanced threat protection setting. ")

    with self.argument_context('mysql flexible-server create') as c:
        c.argument('tier', default='Burstable', arg_type=tier_arg_type)
        c.argument('sku_name', default='Standard_B1ms', arg_type=sku_name_arg_type)
        c.argument('storage_gb', default='32', arg_type=storage_gb_arg_type)
        c.argument('version', default='8.0.21', arg_type=version_arg_type)
        c.argument('iops', arg_type=iops_arg_type)
        c.argument('auto_grow', default='Enabled', arg_type=auto_grow_arg_type)
        c.argument('auto_scale_iops', default='Enabled', arg_type=auto_scale_iops_arg_type)
        c.argument('accelerated_logs', arg_type=accelerated_logs_arg_type)
        c.argument('backup_retention', default=7, arg_type=mysql_backup_retention_arg_type)
        c.argument('backup_byok_identity', arg_type=backup_identity_arg_type)
        c.argument('backup_interval', arg_type=backup_interval_arg_type)
        c.argument('backup_byok_key', arg_type=backup_key_arg_type)
        c.argument('byok_identity', arg_type=identity_arg_type)
        c.argument('byok_key', arg_type=key_arg_type)
        c.argument('geo_redundant_backup', default='Disabled', arg_type=geo_redundant_backup_arg_type)
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('administrator_login', default=generate_username(), arg_type=administrator_login_arg_type)
        c.argument('administrator_login_password', arg_type=administrator_login_password_arg_type)
        c.argument('high_availability', arg_type=high_availability_arg_type, default="Disabled")
        c.argument('public_access', arg_type=public_access_create_arg_type)
        c.argument('vnet', arg_type=vnet_arg_type)
        c.argument('vnet_address_prefix', arg_type=vnet_address_prefix_arg_type)
        c.argument('storage_redundancy', arg_type=storage_redundancy_arg_type, default="LocalRedundancy")
        c.argument('subnet', arg_type=subnet_arg_type)
        c.argument('subnet_address_prefix', arg_type=subnet_address_prefix_arg_type)
        c.argument('private_dns_zone_arguments', private_dns_zone_arguments_arg_type)
        c.argument('zone', zone_arg_type)
        c.argument('tags', tags_type)
        c.argument('standby_availability_zone', arg_type=standby_availability_zone_arg_type)
        c.argument('database_name', arg_type=database_name_arg_type)
        c.argument('database_port', arg_type=database_port_arg_type)
        c.argument('maintenance_policy_patch_strategy', arg_type=maintenance_policy_patch_strategy_arg_type)
        c.argument('yes', arg_type=yes_arg_type)

    with self.argument_context('mysql flexible-server import create') as c:
        c.argument('tier', arg_type=tier_arg_type)
        c.argument('sku_name', arg_type=sku_name_arg_type)
        c.argument('storage_gb', arg_type=storage_gb_arg_type)
        c.argument('version', arg_type=version_arg_type)
        c.argument('iops', arg_type=iops_arg_type)
        c.argument('auto_grow', arg_type=auto_grow_arg_type)
        c.argument('auto_scale_iops', default='Disabled', arg_type=auto_scale_iops_arg_type)
        c.argument('backup_retention', arg_type=mysql_backup_retention_arg_type)
        c.argument('backup_byok_identity', arg_type=backup_identity_arg_type)
        c.argument('backup_byok_key', arg_type=backup_key_arg_type)
        c.argument('byok_identity', arg_type=identity_arg_type)
        c.argument('byok_key', arg_type=key_arg_type)
        c.argument('geo_redundant_backup', arg_type=geo_redundant_backup_arg_type)
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('administrator_login', arg_type=administrator_login_arg_type)
        c.argument('administrator_login_password', arg_type=administrator_login_password_arg_type)
        c.argument('high_availability', arg_type=high_availability_arg_type, default="Disabled")
        c.argument('public_access', arg_type=public_access_create_arg_type)
        c.argument('vnet', arg_type=vnet_arg_type)
        c.argument('vnet_address_prefix', arg_type=vnet_address_prefix_arg_type)
        c.argument('subnet', arg_type=subnet_arg_type)
        c.argument('subnet_address_prefix', arg_type=subnet_address_prefix_arg_type)
        c.argument('private_dns_zone_arguments', private_dns_zone_arguments_arg_type)
        c.argument('zone', zone_arg_type)
        c.argument('tags', tags_type)
        c.argument('standby_availability_zone', arg_type=standby_availability_zone_arg_type)
        c.argument('yes', arg_type=yes_arg_type)
        c.argument('data_source_type', arg_type=data_source_type_arg_type)
        c.argument('data_source', arg_type=data_source_arg_type)
        c.argument('data_source_backup_dir', arg_type=data_source_backup_dir_arg_type)
        c.argument('data_source_sas_token', arg_type=data_source_sas_token_arg_type)
        c.argument('mode', default='Offline', arg_type=mode_arg_type)

    with self.argument_context('mysql flexible-server import stop-replication') as c:
        c.argument('server_name', arg_type=server_name_arg_type)

    with self.argument_context('mysql flexible-server delete') as c:
        c.argument('yes', arg_type=yes_arg_type)

    with self.argument_context('mysql flexible-server restore') as c:
        c.argument('restore_point_in_time', arg_type=restore_point_in_time_arg_type)
        c.argument('source_server', arg_type=source_server_arg_type)
        c.argument('vnet', arg_type=vnet_arg_type)
        c.argument('vnet_address_prefix', arg_type=vnet_address_prefix_arg_type)
        c.argument('subnet', arg_type=subnet_arg_type)
        c.argument('subnet_address_prefix', arg_type=subnet_address_prefix_arg_type)
        c.argument('storage_redundancy', arg_type=storage_redundancy_arg_type)
        c.argument('private_dns_zone_arguments', private_dns_zone_arguments_arg_type)
        c.argument('zone', arg_type=zone_arg_type)
        c.argument('tags', tags_type)
        c.argument('yes', arg_type=yes_arg_type)
        c.argument('sku_name', arg_type=sku_name_arg_type)
        c.argument('tier', arg_type=tier_arg_type)
        c.argument('storage_gb', arg_type=storage_gb_arg_type)
        c.argument('auto_grow', arg_type=auto_grow_arg_type)
        c.argument('accelerated_logs', arg_type=accelerated_logs_arg_type)
        c.argument('faster_restore', arg_type=faster_restore_arg_type)
        c.argument('backup_retention', arg_type=mysql_backup_retention_arg_type)
        c.argument('geo_redundant_backup', arg_type=geo_redundant_backup_arg_type)
        c.argument('database_port', arg_type=database_port_arg_type)
        c.argument('public_access', options_list=['--public-access'], arg_type=get_enum_type(['Enabled', 'Disabled']), help='Determines the public access. ')

    with self.argument_context('mysql flexible-server geo-restore') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), required=True)
        c.argument('sku_name', arg_type=sku_name_arg_type)
        c.argument('source_server', arg_type=source_server_arg_type)
        c.argument('vnet', arg_type=vnet_arg_type)
        c.argument('vnet_address_prefix', arg_type=vnet_address_prefix_arg_type)
        c.argument('subnet', arg_type=subnet_arg_type)
        c.argument('subnet_address_prefix', arg_type=subnet_address_prefix_arg_type)
        c.argument('private_dns_zone_arguments', private_dns_zone_arguments_arg_type)
        c.argument('zone', arg_type=zone_arg_type)
        c.argument('tags', tags_type)
        c.argument('yes', arg_type=yes_arg_type)
        c.argument('sku_name', arg_type=sku_name_arg_type)
        c.argument('tier', arg_type=tier_arg_type)
        c.argument('storage_gb', arg_type=storage_gb_arg_type)
        c.argument('auto_grow', arg_type=auto_grow_arg_type)
        c.argument('accelerated_logs', arg_type=accelerated_logs_arg_type)
        c.argument('storage_redundancy', arg_type=storage_redundancy_arg_type)
        c.argument('backup_retention', arg_type=mysql_backup_retention_arg_type)
        c.argument('geo_redundant_backup', arg_type=geo_redundant_backup_arg_type)
        c.argument('public_access', options_list=['--public-access'], arg_type=get_enum_type(['Enabled', 'Disabled']), help='Determines the public access. ')

    with self.argument_context('mysql flexible-server update') as c:
        c.argument('administrator_login_password', arg_type=administrator_login_password_arg_type)
        c.argument('maintenance_window', options_list=['--maintenance-window'], validator=maintenance_window_validator,
                   help='Period of time (UTC) designated for maintenance. Examples: "Sun:23:30" to schedule on Sunday, 11:30pm UTC. To set back to default pass in "Disabled".')
        c.argument('tags', tags_type)
        c.argument('tier', arg_type=tier_arg_type)
        c.argument('sku_name', arg_type=sku_name_arg_type)
        c.argument('storage_gb', arg_type=storage_gb_arg_type)
        c.argument('standby_availability_zone', arg_type=standby_availability_zone_arg_type)
        c.argument('high_availability', arg_type=high_availability_arg_type)
        c.argument('backup_interval', arg_type=backup_interval_arg_type)
        c.argument('byok_key', arg_type=key_arg_type)
        c.argument('byok_identity', arg_type=identity_arg_type)
        c.argument('auto_grow', arg_type=auto_grow_arg_type)
        c.argument('auto_scale_iops', arg_type=auto_scale_iops_arg_type)
        c.argument('accelerated_logs', arg_type=accelerated_logs_arg_type)
        c.argument('replication_role', options_list=['--replication-role'], help='The replication role of the server.')
        c.argument('iops', arg_type=iops_arg_type)
        c.argument('backup_retention', arg_type=mysql_backup_retention_arg_type)
        c.argument('geo_redundant_backup', arg_type=geo_redundant_backup_arg_type)
        c.argument('backup_byok_identity', arg_type=backup_identity_arg_type)
        c.argument('backup_byok_key', arg_type=backup_key_arg_type)
        c.argument('disable_data_encryption', arg_type=disable_data_encryption_arg_type)
        c.argument('public_access', arg_type=public_access_update_arg_type)
        c.argument('maintenance_policy_patch_strategy', arg_type=maintenance_policy_patch_strategy_arg_type)

    with self.argument_context('mysql flexible-server upgrade') as c:
        c.argument('version', arg_type=mysql_version_upgrade_arg_type)
        c.argument('yes', arg_type=yes_arg_type)

    with self.argument_context('mysql flexible-server restart') as c:
        c.argument('fail_over', options_list=['--failover'], help='Forced failover for server restart operation. Allowed values: Forced')

    with self.argument_context('mysql flexible-server list-skus') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx))

    with self.argument_context('mysql flexible-server detach-vnet') as c:
        c.argument('public_network_access', options_list=['--public-network-access'], arg_type=get_enum_type(['Enabled', 'Disabled']), help='Determines the public access after vnet detach. ')
        c.argument('yes', arg_type=yes_arg_type)

    # flexible-server parameter
    for scope in ['list', 'set', 'show', 'set-batch']:
        argument_context_string = 'mysql flexible-server parameter {}'.format(scope)
        with self.argument_context(argument_context_string) as c:
            if scope == "list":
                c.argument('server_name', options_list=['--server-name', '-s'], id_part=None, arg_type=server_name_arg_type)
            else:
                c.argument('server_name', options_list=['--server-name', '-s'], arg_type=server_name_arg_type)

    for scope in ['show', 'set']:
        argument_context_string = 'mysql flexible-server parameter {}'.format(scope)
        with self.argument_context(argument_context_string) as c:
            c.argument('configuration_name', id_part='child_name_1', options_list=['--name', '-n'], required=True, help='The name of the server configuration')

    with self.argument_context('mysql flexible-server parameter set') as c:
        c.argument('value', options_list=['--value', '-v'], help='Value of the configuration.')
        c.argument('source', options_list=['--source'], help='Source of the configuration.')

    with self.argument_context('mysql flexible-server parameter set-batch') as c:
        c.argument('configuration_list', action=AddArgs, nargs='*', options_list=['--args'], required=True, help='List of the configuration key-value pair.')
        c.argument('source', options_list=['--source'], required=False, help='Source of the configuration.')

    # firewall-rule
    for scope in ['create', 'delete', 'list', 'show', 'update']:
        argument_context_string = 'mysql flexible-server firewall-rule {}'.format(scope)
        with self.argument_context(argument_context_string) as c:
            c.argument('resource_group_name', arg_type=resource_group_name_type)
            if scope == "list":
                c.argument('server_name', id_part=None, arg_type=server_name_arg_type)
            else:
                c.argument('server_name', id_part='name', arg_type=server_name_arg_type)

    for scope in ['create', 'delete', 'show', 'update']:
        argument_context_string = 'mysql flexible-server firewall-rule {}'.format(scope)
        with self.argument_context(argument_context_string) as c:
            c.argument('firewall_rule_name', id_part='child_name_1', options_list=['--rule-name', '-r'], validator=firewall_rule_name_validator,
                       help='The name of the firewall rule. If name is omitted, default name will be chosen for firewall name. The firewall rule name can only contain 0-9, a-z, A-Z, \'-\' and \'_\'. Additionally, the name of the firewall rule must be at least 1 character and no more than 80 characters in length. ')
            c.argument('end_ip_address', options_list=['--end-ip-address'], validator=ip_address_validator,
                       help='The end IP address of the firewall rule. Must be IPv4 format. Use value \'0.0.0.0\' to represent all Azure-internal IP addresses. ')
            c.argument('start_ip_address', options_list=['--start-ip-address'], validator=ip_address_validator,
                       help='The start IP address of the firewall rule. Must be IPv4 format. Use value \'0.0.0.0\' to represent all Azure-internal IP addresses. ')

    with self.argument_context('mysql flexible-server firewall-rule delete') as c:
        c.argument('yes', arg_type=yes_arg_type)

    # db
    for scope in ['create', 'delete', 'list', 'show', 'update']:
        argument_context_string = 'mysql flexible-server db {}'.format(scope)
        with self.argument_context(argument_context_string) as c:
            c.argument('server_name', options_list=['--server-name', '-s'], arg_type=server_name_arg_type)
            c.argument('database_name', arg_type=database_name_arg_type)

    with self.argument_context('mysql flexible-server db list') as c:
        c.argument('server_name', id_part=None, options_list=['--server-name', '-s'], arg_type=server_name_arg_type)

    with self.argument_context('mysql flexible-server db create') as c:
        c.argument('charset', help='The charset of the database. The default value is UTF8')
        c.argument('collation', help='The collation of the database.')

    with self.argument_context('mysql flexible-server db delete') as c:
        c.argument('yes', arg_type=yes_arg_type)

    with self.argument_context('mysql flexible-server show-connection-string') as c:
        c.argument('server_name', options_list=['--server-name', '-s'], arg_type=server_name_arg_type)
        c.argument('administrator_login', arg_type=administrator_login_arg_type,)
        c.argument('administrator_login_password', arg_type=administrator_login_password_arg_type)
        c.argument('database_name', arg_type=database_name_arg_type)

    with self.argument_context('mysql flexible-server replica list') as c:
        c.argument('server_name', id_part=None, options_list=['--name', '-n'], help='Name of the source server.')

    with self.argument_context('mysql flexible-server replica create') as c:
        c.argument('source_server', arg_type=source_server_arg_type)
        c.argument('replica_name', options_list=['--replica-name'], help='The name of the server to restore to.')
        c.argument('zone', arg_type=zone_arg_type)
        c.argument('tags', tags_type)
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('vnet', arg_type=vnet_arg_type)
        c.argument('subnet', arg_type=subnet_arg_type)
        c.argument('private_dns_zone_arguments', private_dns_zone_arguments_arg_type)
        c.argument('public_access', options_list=['--public-access'], arg_type=get_enum_type(['Enabled', 'Disabled']), help='Determines the public access. ')
        c.argument('tier', arg_type=tier_arg_type)
        c.argument('sku_name', arg_type=sku_name_arg_type)
        c.argument('storage_gb', arg_type=storage_gb_arg_type)
        c.argument('iops', arg_type=iops_arg_type)
        c.argument('storage_redundancy', arg_type=storage_redundancy_arg_type, default="LocalRedundancy")
        c.argument('faster_provisioning', arg_type=faster_provisioning_arg_type)
        c.argument('database_port', arg_type=database_port_arg_type)
        c.argument('backup_retention', arg_type=mysql_backup_retention_arg_type)
        c.argument('geo_redundant_backup', arg_type=geo_redundant_backup_arg_type)

    with self.argument_context('mysql flexible-server replica stop-replication') as c:
        c.argument('server_name', arg_type=server_name_arg_type)

    with self.argument_context('mysql flexible-server deploy setup') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('server_name', options_list=['--server-name', '-s'], arg_type=server_name_arg_type)
        c.argument('database_name', arg_type=database_name_arg_type)
        c.argument('administrator_login', arg_type=administrator_login_arg_type)
        c.argument('administrator_login_password', arg_type=administrator_login_password_arg_type)
        c.argument('sql_file_path', options_list=['--sql-file'], help='The path of the sql file. The sql file should be already in the repository')
        c.argument('action_name', options_list=['--action-name'], help='The name of the github action')
        c.argument('repository', options_list=['--repo'], help='The name of your github username and repository e.g., Azure/azure-cli ')
        c.argument('branch', options_list=['--branch'], help='The name of the branch you want upload github action file. The default will be your current branch.')
        c.argument('allow_push', default=False, options_list=['--allow-push'], arg_type=get_three_state_flag(), help='Push the action yml file to the remote repository. The changes will be pushed to origin repository, speicified branch or current branch if not specified.')

    with self.argument_context('mysql flexible-server deploy run') as c:
        c.argument('action_name', options_list=['--action-name'], help='The name of the github action', validator=validate_action_name)
        c.argument('branch', options_list=['--branch'], help='The name of the branch you want upload github action file. The default will be your current branch.', validator=validate_branch)

    with self.argument_context('mysql flexible-server server-logs download') as c:
        c.argument('server_name', id_part=None, options_list=['--server-name', '-s'], arg_type=server_name_arg_type)
        c.argument('file_name', options_list=['--name', '-n'], nargs='+', help='Space-separated list of log filenames on the server to download.')

    with self.argument_context('mysql flexible-server server-logs list') as c:
        c.argument('server_name', id_part=None, options_list=['--server-name', '-s'], arg_type=server_name_arg_type)
        c.argument('filename_contains', help='The pattern that file name should match.')
        c.argument('file_last_written', type=int, help='Integer in hours to indicate file last modify time.', default=72)
        c.argument('max_file_size', type=int, help='The file size limitation to filter files.')

    # backups
    with self.argument_context('mysql flexible-server backup create') as c:
        c.argument('backup_name', options_list=['--backup-name', '-b'], help='The name of the new backup.')

    with self.argument_context('mysql flexible-server backup delete') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('server_name', id_part=None, arg_type=server_name_arg_type)
        c.argument('backup_name', options_list=['--backup-name', '-b'], help='The name of the backup.')

    with self.argument_context('mysql flexible-server backup show') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('server_name', id_part=None, arg_type=server_name_arg_type)
        c.argument('backup_name', options_list=['--backup-name', '-b'], help='The name of the backup.')

    with self.argument_context('mysql flexible-server backup list') as c:
        c.argument('server_name', id_part=None, arg_type=server_name_arg_type)

    # export
    with self.argument_context('mysql flexible-server export create') as c:
        c.argument('backup_name', options_list=['--backup-name', '-b'], help='The name of the new export backup.')
        c.argument('sas_uri', options_list=['--sas-uri', '-u'], help='SAS URI for destination container.')

    # identity
    with self.argument_context('mysql flexible-server identity') as c:
        c.argument('server_name', id_part=None, options_list=['--server-name', '-s'], arg_type=server_name_arg_type)

    with self.argument_context('mysql flexible-server identity assign') as c:
        c.argument('identities', arg_type=identities_arg_type)

    with self.argument_context('mysql flexible-server identity remove') as c:
        c.argument('identities', arg_type=identities_arg_type)

    with self.argument_context('mysql flexible-server identity show') as c:
        c.argument('identity', options_list=['--identity', '-n'], help='Name or ID of identity to show.', validator=validate_identity)

    with self.argument_context('mysql flexible-server maintenance reschedule') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type, help='Resource Group Name of the server.')
        c.argument('server_name', options_list=['--server-name', '-s'], help='The name of the server.')
        c.argument('maintenance_name', options_list=['--maintenance-name', '-m'], help='The name of the maintenance.')
        c.argument('maintenance_start_time', arg_type=maintenance_reschedule_time_arg_type, help='The new start time of the rescheduled maintenance.')

    with self.argument_context('mysql flexible-server maintenance list') as c:
        c.argument('resource_group_name', id_part=None, arg_type=resource_group_name_type, help='Resource Group Name of the server.')
        c.argument('server_name', id_part=None, options_list=['--server-name', '-s'], help='The name of the server.')

    with self.argument_context('mysql flexible-server maintenance show') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type, help='Resource Group Name of the server.')
        c.argument('server_name', options_list=['--server-name', '-s'], help='The name of the server.')
        c.argument('maintenance_name', options_list=['--maintenance-name', '-m'], help='The name of the maintenance.')

    # ad-admin
    with self.argument_context('mysql flexible-server ad-admin') as c:
        c.argument('server_name', id_part=None, options_list=['--server-name', '-s'], arg_type=server_name_arg_type)

    for scope in ['create', 'show', 'delete', 'wait']:
        with self.argument_context('mysql flexible-server ad-admin {}'.format(scope)) as c:
            c.argument('sid', options_list=['--object-id', '-i'], help='The unique ID of the Azure AD administrator.')

    with self.argument_context('mysql flexible-server ad-admin create') as c:
        c.argument('login', options_list=['--display-name', '-u'], help='Display name of the Azure AD administrator user or group.')
        c.argument('principal_type', options_list=['--type', '-t'], default='User', arg_type=get_enum_type(['User', 'Group', 'ServicePrincipal', 'Unknown']), help='Type of the Azure AD administrator.')
        c.argument('identity', help='Name or ID of identity used for AAD Authentication.', validator=validate_identity)

    # GTID
    with self.argument_context('mysql flexible-server gtid reset') as c:
        c.argument('gtid_set', arg_type=gtid_set_arg_type)
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('server_name', id_part=None, options_list=['--server-name', '-s'], arg_type=server_name_arg_type)
        c.argument('yes', arg_type=yes_arg_type)

    for scope in ['create', 'show', 'list', 'update', 'delete', 'check-name-availability']:
        argument_context_string = 'mysql flexible-server migration {}'.format(scope)
        with self.argument_context(argument_context_string) as c:
            c.argument('resource_group_name', arg_type=resource_group_name_type,
                       help='Resource Group Name of the migration target server.')
            c.argument('server_name', id_part='name', options_list=['--name', '-n'], arg_type=server_name_arg_type,
                       help='Migration target server name.')
            if scope == "create":
                c.argument('properties', type=file_type, completer=FilesCompleter(), options_list=['--properties', '-b'],
                           help='Request properties. Use double or no quotes to pass in filepath as argument.')
                c.argument('migration_name', arg_type=migration_id_arg_type, options_list=['--migration-name'],
                           help='Name of the migration.')
                c.argument('migration_mode', arg_type=migration_id_arg_type, options_list=['--migration-mode'], required=False,
                           help='Either offline or online(with CDC) migration', choices=['offline', 'online'], default='offline')
            elif scope == "show":
                c.argument('migration_name', arg_type=migration_id_arg_type, options_list=['--migration-name'],
                           help='Name of the migration.')
            elif scope == "list":
                c.argument('server_name', id_part=None, arg_type=server_name_arg_type)
                c.argument('migration_filter', options_list=['--filter'], required=False, choices=['Active', 'All'], default='Active',
                           help='Indicate whether all the migrations or just the Active migrations are returned. Valid values are: Active and All.')
            elif scope == "update":
                c.argument('migration_name', arg_type=migration_id_arg_type, options_list=['--migration-name'],
                           help='Name of the migration.')
                c.argument('setup_logical_replication', options_list=['--setup-replication'], action='store_true', required=False,
                           help='Allow the migration workflow to setup logical replication on the source. Note that this command will restart the source server.')
                c.argument('db_names', nargs='+', options_list=['--db-names', '--dbs'], required=False,
                           help='Space-separated list of DBs to migrate. Note that each additional DB affects the performance of the source server.')
                c.argument('overwrite_dbs', options_list=['--overwrite-dbs'], action='store_true', required=False,
                           help='Allow the migration workflow to overwrite the DB on the target.')
                c.argument('cutover', options_list=['--cutover'], required=False, action='store_true',
                           help='Cut-over the data migration for all the databases in the migration. After this is complete, subsequent updates to all databases will not be migrated to the target.')
                c.argument('cancel', options_list=['--cancel'], required=False, action='store_true',
                           help='Cancel the data migration for all the databases.')
            elif scope == "check-name-availability":
                c.argument('migration_name', arg_type=migration_id_arg_type, options_list=['--migration-name'],
                           help='Name of the migration.')
