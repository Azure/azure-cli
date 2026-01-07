# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (
    tags_type, get_location_type,
    get_enum_type, file_type,
    resource_group_name_type,
    get_three_state_flag)
from azure.cli.command_modules.postgresql.validators import public_access_validator, maintenance_window_validator, ip_address_validator, \
    retention_validator, validate_identity, validate_byok_identity, validate_identities, \
    virtual_endpoint_name_validator, node_count_validator, postgres_firewall_rule_name_validator, \
    db_renaming_cluster_validator
from azure.cli.core.local_context import LocalContextAttribute, LocalContextAction

from .randomname.generate import generate_username
from ._flexible_server_util import get_current_time
from argcomplete.completers import FilesCompleter
from ._util import get_autonomous_tuning_settings_map


def load_arguments(self, _):    # pylint: disable=too-many-statements, too-many-locals

    # Flexible-server
    # pylint: disable=too-many-locals, too-many-branches
    def _flexible_server_params(command_group):

        server_name_arg_type = CLIArgumentType(
            metavar='NAME',
            options_list=['--name', '-n'],
            id_part='name',
            help="Name of the server. The name can contain only lowercase letters, numbers, and the hyphen (-) character. Minimum 3 characters and maximum 63 characters.",
            local_context_attribute=LocalContextAttribute(
                name='server_name',
                actions=[LocalContextAction.SET, LocalContextAction.GET],
                scopes=['{} flexible-server'.format(command_group)]))

        server_name_resource_arg_type = CLIArgumentType(
            metavar='NAME',
            options_list=['--server-name', '-s'],
            id_part='name',
            help="Name of the server.",
            local_context_attribute=LocalContextAttribute(
                name='server_name',
                actions=[LocalContextAction.SET, LocalContextAction.GET],
                scopes=['{} flexible-server'.format(command_group)]))

        replica_name_arg_type = CLIArgumentType(
            metavar='NAME',
            options_list=['--name', '-n'],
            id_part='name',
            help="Name of the read replica.",
            local_context_attribute=LocalContextAttribute(
                name='server_name',
                actions=[LocalContextAction.SET, LocalContextAction.GET],
                scopes=['{} flexible-server'.format(command_group)]))

        migration_id_arg_type = CLIArgumentType(
            metavar='NAME',
            help="ID of the migration.",
            local_context_attribute=LocalContextAttribute(
                name='migration_id',
                actions=[LocalContextAction.SET, LocalContextAction.GET],
                scopes=['{} flexible-server'.format(command_group)]))

        administrator_login_arg_type = CLIArgumentType(
            options_list=['--admin-user', '-u'],
            arg_group='Authentication',
            help='Administrator username for the server. Once set, it cannot be changed. ',
            local_context_attribute=LocalContextAttribute(
                name='administrator_login',
                actions=[LocalContextAction.GET, LocalContextAction.SET],
                scopes=['{} flexible-server'.format(command_group)]))

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
            help='The name of the database',
            local_context_attribute=LocalContextAttribute(
                name='database_name',
                actions=[LocalContextAction.GET, LocalContextAction.SET],
                scopes=['{} flexible-server'.format(command_group)]))

        database_name_arg_type_cluster = CLIArgumentType(
            metavar='NAME',
            options_list=['--database-name', '-d'],
            help='The default database name for an elastic cluster. Only applicable when --cluster-option is set to ElasticCluster.',
            local_context_attribute=LocalContextAttribute(
                name='database_name',
                actions=[LocalContextAction.GET, LocalContextAction.SET],
                scopes=['{} flexible-server'.format(command_group)]),
            validator=db_renaming_cluster_validator)

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

        pg_backup_retention_arg_type = CLIArgumentType(
            type=int,
            options_list=['--backup-retention'],
            help='The number of days a backup is retained. Range of 7 to 35 days. Default is 7 days.',
            validator=retention_validator
        )

        version_arg_type = CLIArgumentType(
            options_list=['--version'],
            help='Server major version.'
        )

        iops_v2_arg_type = CLIArgumentType(
            type=int,
            options_list=['--iops'],
            help='Value of IOPS in (operations/sec) to be allocated for this server. '
                 'This value can only be updated if flexible server is using Premium SSD v2 Disks.'
        )

        throughput_arg_type = CLIArgumentType(
            type=int,
            options_list=['--throughput'],
            help='Storage throughput in (MB/sec) for the server. '
                 'This value can only be updated if flexible server is using Premium SSD v2 Disks.'
        )

        cluster_option_arg_type = CLIArgumentType(
            arg_type=get_enum_type(['Server', 'ElasticCluster']),
            options_list=['--cluster-option'],
            help='Cluster option for the server. Servers are for workloads that can fit on one node. '
                 'Elastic clusters provides schema- and row-based sharding on a database. Default value is Server.'
        )

        create_node_count_arg_type = CLIArgumentType(
            type=int,
            options_list=['--node-count'],
            help='The number of nodes for elastic cluster. Range of 1 to 10. Default is 2 nodes.',
            validator=node_count_validator
        )

        update_node_count_arg_type = CLIArgumentType(
            type=int,
            options_list=['--node-count'],
            help='The number of nodes for elastic cluster. Range of 1 to 10.',
            validator=node_count_validator
        )

        auto_grow_arg_type = CLIArgumentType(
            arg_type=get_enum_type(['Enabled', 'Disabled']),
            options_list=['--storage-auto-grow'],
            help='Enable or disable autogrow of the storage. Default value is Enabled.'
        )

        storage_type_arg_type = CLIArgumentType(
            arg_type=get_enum_type(['PremiumV2_LRS', 'Premium_LRS']),
            options_list=['--storage-type'],
            help='Storage type for the server. Allowed values are Premium_LRS and PremiumV2_LRS. Default value is Premium_LRS.'
                 'Must set iops and throughput if using PremiumV2_LRS.'
        )

        storage_type_restore_arg_type = CLIArgumentType(
            arg_type=get_enum_type(['PremiumV2_LRS']),
            options_list=['--storage-type'],
            help='Storage type for the new server. Allowed value is PremiumV2_LRS. Default value is none.'
        )

        performance_tier_arg_type = CLIArgumentType(
            options_list=['--performance-tier'],
            help='Performance tier of the server.'
        )

        yes_arg_type = CLIArgumentType(
            options_list=['--yes', '-y'],
            action='store_true',
            help='Do not prompt for confirmation.'
        )

        vnet_arg_type = CLIArgumentType(
            options_list=['--vnet'],
            help='Name or ID of a new or existing virtual network. '
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
                 'Setting it to "None" sets the server in public access mode but does not create a firewall rule. '
                 'Acceptable values are \'Disabled\', \'Enabled\', \'All\', \'None\',\'{startIP}\' and '
                 '\'{startIP}-{destinationIP}\' where startIP and destinationIP ranges from '
                 '0.0.0.0 to 255.255.255.255. ',
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

        zonal_resiliency_arg_type = CLIArgumentType(
            arg_type=get_enum_type(['Enabled', 'Disabled']),
            options_list=['--zonal-resiliency'],
            help='Enable or disable high availability feature.'
        )

        allow_same_zone_arg_type = CLIArgumentType(
            options_list=['--allow-same-zone'],
            action='store_true',
            help='Allow primary and standby in the same zone when multi-zone capacity is unavailable.'
        )

        pg_version_upgrade_arg_type = CLIArgumentType(
            arg_type=get_enum_type(['13', '14', '15', '16', '17', '18']),
            options_list=['--version', '-v'],
            help='Server major version.'
        )

        private_dns_zone_arguments_arg_type = CLIArgumentType(
            options_list=['--private-dns-zone'],
            help='This parameter only applies for a server with private access. '
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

        key_arg_type = CLIArgumentType(
            options_list=['--key'],
            help='The resource ID of the primary keyvault key for data encryption.'
        )

        backup_key_arg_type = CLIArgumentType(
            options_list=['--backup-key'],
            help='The resource ID of the geo backup keyvault key for data encryption. The key needs to be in the same region as the backup region.'
        )

        identities_arg_type = CLIArgumentType(
            options_list=['--identity', '-n'],
            nargs='+',
            help='Space-separated names or ID\'s of identities.',
            validator=validate_identities
        )

        microsoft_entra_auth_arg_type = CLIArgumentType(
            options_list=['--microsoft-entra-auth'],
            arg_type=get_enum_type(['Enabled', 'Disabled']),
            help='Whether Microsoft Entra authentication is enabled.'
        )

        password_auth_arg_type = CLIArgumentType(
            options_list=['--password-auth'],
            arg_type=get_enum_type(['Enabled', 'Disabled']),
            help='Whether password authentication is enabled.'
        )

        pg_bouncer_arg_type = CLIArgumentType(
            options_list=['--pg-bouncer'],
            action='store_true',
            help='Show connection strings for PgBouncer.'
        )

        promote_mode_arg_type = CLIArgumentType(
            arg_type=get_enum_type(['standalone', 'switchover']),
            help='Whether to promote read replica to an independent server or promote it as a primary server.'
        )

        promote_option_arg_type = CLIArgumentType(
            arg_type=get_enum_type(['planned', 'forced']),
            help='Whether to sync data before promoting read replica or promote as soon as possible.'
        )

        virtual_endpoint_arg_type = CLIArgumentType(
            metavar='NAME',
            options_list=['--name', '-n'],
            id_part='name',
            help="Name of the virtual endpoint. The name can contain only lowercase letters, numbers, and the hyphen (-) character. Minimum 3 characters and maximum 63 characters.",
            local_context_attribute=LocalContextAttribute(
                name='virtual_endpoint_name',
                actions=[LocalContextAction.SET, LocalContextAction.GET],
                scopes=['{} flexible-server'.format(command_group)]))

        endpoint_type_arg_type = CLIArgumentType(
            options_list=['--endpoint-type', '-t'],
            arg_type=get_enum_type(['ReadWrite']),
            help='Type of connection point for virtual endpoint.'
        )

        members_type = CLIArgumentType(
            options_list=['--members', '-m'],
            help='The read replicas the virtual endpoints point to.'
        )

        with self.argument_context('{} flexible-server'.format(command_group)) as c:
            c.argument('resource_group_name', arg_type=resource_group_name_type)
            c.argument('server_name', arg_type=server_name_arg_type)

        with self.argument_context('{} flexible-server create'.format(command_group)) as c:
            # Add create mode as a parameter
            c.argument('tier', default='GeneralPurpose', arg_type=tier_arg_type)
            c.argument('sku_name', arg_type=sku_name_arg_type)
            c.argument('storage_gb', default='128', arg_type=storage_gb_arg_type)
            c.argument('version', arg_type=version_arg_type)
            c.argument('backup_retention', default=7, arg_type=pg_backup_retention_arg_type)
            c.argument('microsoft_entra_auth', default='Disabled', arg_type=microsoft_entra_auth_arg_type)
            c.argument('admin_id', options_list=['--admin-object-id', '-i'], help='The unique ID of the Microsoft Entra administrator.')
            c.argument('admin_name', options_list=['--admin-display-name', '-m'], help='Display name of the Microsoft Entra administrator user or group.')
            c.argument('admin_type', options_list=['--admin-type', '-t'],
                       arg_type=get_enum_type(['User', 'Group', 'ServicePrincipal', 'Unknown']), help='Type of the Microsoft Entra administrator.')
            c.argument('password_auth', default='Enabled', arg_type=password_auth_arg_type)
            c.argument('auto_grow', default='Disabled', arg_type=auto_grow_arg_type)
            c.argument('storage_type', default=None, arg_type=storage_type_arg_type)
            c.argument('iops', default=None, arg_type=iops_v2_arg_type)
            c.argument('throughput', default=None, arg_type=throughput_arg_type)
            c.argument('performance_tier', default=None, arg_type=performance_tier_arg_type)
            c.argument('create_cluster', default='Server', arg_type=cluster_option_arg_type)
            c.argument('cluster_size', default=None, arg_type=create_node_count_arg_type)
            c.argument('zonal_resiliency', arg_type=zonal_resiliency_arg_type, default="Disabled")
            c.argument('allow_same_zone', arg_type=allow_same_zone_arg_type, default=False)
            c.argument('database_name', default=None, arg_type=database_name_arg_type_cluster)
            c.argument('byok_identity', arg_type=identity_arg_type)
            c.argument('byok_key', arg_type=key_arg_type)
            c.argument('backup_byok_identity', arg_type=backup_identity_arg_type)
            c.argument('backup_byok_key', arg_type=backup_key_arg_type)
            c.argument('geo_redundant_backup', default='Disabled', arg_type=geo_redundant_backup_arg_type)
            c.argument('location', arg_type=get_location_type(self.cli_ctx))
            c.argument('administrator_login', default=generate_username(), arg_type=administrator_login_arg_type)
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

        with self.argument_context('{} flexible-server list'.format(command_group)) as c:
            c.argument('show_cluster', options_list=['--show-cluster'], required=False, action='store_true',
                       help='Only show elastic clusters.')

        with self.argument_context('{} flexible-server delete'.format(command_group)) as c:
            c.argument('yes', arg_type=yes_arg_type)

        with self.argument_context('{} flexible-server restore'.format(command_group)) as c:
            c.argument('restore_point_in_time', arg_type=restore_point_in_time_arg_type)
            c.argument('source_server', arg_type=source_server_arg_type)
            c.argument('vnet', arg_type=vnet_arg_type)
            c.argument('vnet_address_prefix', arg_type=vnet_address_prefix_arg_type)
            c.argument('subnet', arg_type=subnet_arg_type)
            c.argument('subnet_address_prefix', arg_type=subnet_address_prefix_arg_type)
            c.argument('private_dns_zone_arguments', private_dns_zone_arguments_arg_type)
            c.argument('zone', arg_type=zone_arg_type)
            c.argument('yes', arg_type=yes_arg_type)
            c.argument('byok_key', arg_type=key_arg_type)
            c.argument('byok_identity', arg_type=identity_arg_type)
            c.argument('geo_redundant_backup', default='Disabled', arg_type=geo_redundant_backup_arg_type)
            c.argument('backup_byok_identity', arg_type=backup_identity_arg_type)
            c.argument('backup_byok_key', arg_type=backup_key_arg_type)
            c.argument('storage_type', default=None, arg_type=storage_type_restore_arg_type)

        with self.argument_context('{} flexible-server geo-restore'. format(command_group)) as c:
            c.argument('location', arg_type=get_location_type(self.cli_ctx), required=True)
            c.argument('sku_name', arg_type=sku_name_arg_type)
            c.argument('source_server', arg_type=source_server_arg_type)
            c.argument('vnet', arg_type=vnet_arg_type)
            c.argument('vnet_address_prefix', arg_type=vnet_address_prefix_arg_type)
            c.argument('subnet', arg_type=subnet_arg_type)
            c.argument('subnet_address_prefix', arg_type=subnet_address_prefix_arg_type)
            c.argument('private_dns_zone_arguments', private_dns_zone_arguments_arg_type)
            c.argument('zone', arg_type=zone_arg_type)
            c.argument('yes', arg_type=yes_arg_type)
            c.argument('restore_point_in_time', arg_type=restore_point_in_time_arg_type)
            c.argument('geo_redundant_backup', default='Disabled', arg_type=geo_redundant_backup_arg_type)
            c.argument('byok_key', arg_type=key_arg_type)
            c.argument('byok_identity', arg_type=identity_arg_type)
            c.argument('backup_byok_identity', arg_type=backup_identity_arg_type)
            c.argument('backup_byok_key', arg_type=backup_key_arg_type)

        with self.argument_context('{} flexible-server revive-dropped'. format(command_group)) as c:
            c.argument('location', arg_type=get_location_type(self.cli_ctx), required=True)
            c.argument('sku_name', arg_type=sku_name_arg_type)
            c.argument('source_server', arg_type=source_server_arg_type)
            c.argument('vnet', arg_type=vnet_arg_type)
            c.argument('vnet_address_prefix', arg_type=vnet_address_prefix_arg_type)
            c.argument('subnet', arg_type=subnet_arg_type)
            c.argument('subnet_address_prefix', arg_type=subnet_address_prefix_arg_type)
            c.argument('private_dns_zone_arguments', private_dns_zone_arguments_arg_type)
            c.argument('zone', arg_type=zone_arg_type)
            c.argument('yes', arg_type=yes_arg_type)
            c.argument('geo_redundant_backup', default='Disabled', arg_type=geo_redundant_backup_arg_type)
            c.argument('byok_key', arg_type=key_arg_type)
            c.argument('byok_identity', arg_type=identity_arg_type)
            c.argument('backup_byok_identity', arg_type=backup_identity_arg_type)
            c.argument('backup_byok_key', arg_type=backup_key_arg_type)

        with self.argument_context('{} flexible-server update'.format(command_group)) as c:
            c.argument('administrator_login_password', arg_type=administrator_login_password_arg_type)
            c.argument('maintenance_window', options_list=['--maintenance-window'], validator=maintenance_window_validator,
                       help='Period of time (UTC) designated for maintenance. Examples: "Sun:23:30" to schedule on Sunday, 11:30pm UTC. To set back to default pass in "Disabled".')
            c.argument('tags', tags_type)
            c.argument('tier', arg_type=tier_arg_type)
            c.argument('sku_name', arg_type=sku_name_arg_type)
            c.argument('storage_gb', arg_type=storage_gb_arg_type)
            c.argument('standby_availability_zone', arg_type=standby_availability_zone_arg_type)
            c.argument('high_availability', arg_type=high_availability_arg_type)
            c.argument('byok_key', arg_type=key_arg_type)
            c.argument('byok_identity', arg_type=identity_arg_type)
            c.argument('backup_byok_identity', arg_type=backup_identity_arg_type)
            c.argument('backup_byok_key', arg_type=backup_key_arg_type)
            c.argument('public_access', arg_type=public_access_update_arg_type)
            c.argument('auto_grow', arg_type=auto_grow_arg_type)
            c.argument('performance_tier', default=None, arg_type=performance_tier_arg_type)
            c.argument('iops', default=None, arg_type=iops_v2_arg_type)
            c.argument('throughput', default=None, arg_type=throughput_arg_type)
            c.argument('backup_retention', arg_type=pg_backup_retention_arg_type)
            c.argument('microsoft_entra_auth', arg_type=microsoft_entra_auth_arg_type)
            c.argument('password_auth', arg_type=password_auth_arg_type)
            c.argument('private_dns_zone_arguments', private_dns_zone_arguments_arg_type)
            c.argument('cluster_size', default=None, arg_type=update_node_count_arg_type)
            c.argument('zonal_resiliency', arg_type=zonal_resiliency_arg_type)
            c.argument('allow_same_zone', arg_type=allow_same_zone_arg_type)
            c.argument('yes', arg_type=yes_arg_type)

        with self.argument_context('{} flexible-server upgrade'.format(command_group)) as c:
            c.argument('version', arg_type=pg_version_upgrade_arg_type)
            c.argument('yes', arg_type=yes_arg_type)

        with self.argument_context('{} flexible-server restart'.format(command_group)) as c:
            c.argument('fail_over', options_list=['--failover'],
                       help='Forced or planned failover for server restart operation. Allowed values: Forced, Planned')

        with self.argument_context('{} flexible-server list-skus'.format(command_group)) as c:
            c.argument('location', arg_type=get_location_type(self.cli_ctx))

        # flexible-server parameter
        for scope in ['list', 'set', 'show']:
            argument_context_string = '{} flexible-server parameter {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('server_name', arg_type=server_name_resource_arg_type)

        for scope in ['show', 'set']:
            argument_context_string = '{} flexible-server parameter {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('configuration_name', id_part='child_name_1', options_list=['--name', '-n'], required=True,
                           help='The name of the server configuration')

        with self.argument_context('{} flexible-server parameter set'.format(command_group)) as c:
            c.argument('value', options_list=['--value', '-v'],
                       help='Value of the configuration.')
            c.argument('source', options_list=['--source'],
                       help='Source of the configuration.')

        # firewall-rule
        for scope in ['create', 'delete', 'show', 'update']:
            argument_context_string = '{} flexible-server firewall-rule {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('firewall_rule_name', id_part='child_name_1', options_list=['--rule-name', '-r'], validator=postgres_firewall_rule_name_validator,
                           help='The name of the firewall rule. If name is omitted, default name will be chosen for firewall name. The firewall rule name can only contain 0-9, a-z, A-Z, \'-\' and \'_\'. Additionally, the name of the firewall rule must be at least 3 characters and no more than 128 characters in length. ')
                c.argument('end_ip_address', options_list=['--end-ip-address'], validator=ip_address_validator,
                           help='The end IP address of the firewall rule. Must be IPv4 format. Use value \'0.0.0.0\' to represent all Azure-internal IP addresses. ')
                c.argument('start_ip_address', options_list=['--start-ip-address'], validator=ip_address_validator,
                           help='The start IP address of the firewall rule. Must be IPv4 format. Use value \'0.0.0.0\' to represent all Azure-internal IP addresses. ')

        with self.argument_context('{} flexible-server firewall-rule delete'.format(command_group)) as c:
            c.argument('yes', arg_type=yes_arg_type)

        # db
        for scope in ['create', 'delete', 'list', 'show', 'update']:
            argument_context_string = '{} flexible-server db {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('server_name', arg_type=server_name_resource_arg_type)
                c.argument('database_name', arg_type=database_name_arg_type)

        with self.argument_context('{} flexible-server db create'.format(command_group)) as c:
            c.argument('charset', help='The charset of the database. The default value is UTF8')
            c.argument('collation', help='The collation of the database.')

        with self.argument_context('{} flexible-server db delete'.format(command_group)) as c:
            c.argument('yes', arg_type=yes_arg_type)

        with self.argument_context('{} flexible-server show-connection-string'.format(command_group)) as c:
            c.argument('server_name', arg_type=server_name_resource_arg_type)
            c.argument('administrator_login', arg_type=administrator_login_arg_type,)
            c.argument('administrator_login_password', arg_type=administrator_login_password_arg_type)
            c.argument('database_name', arg_type=database_name_arg_type)
            c.argument('show_pg_bouncer', arg_type=pg_bouncer_arg_type)

        # virtual-endpoint
        for scope in ['create', 'delete', 'list', 'show', 'update']:
            argument_context_string = '{} flexible-server virtual-endpoint {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('server_name', arg_type=server_name_resource_arg_type)
                c.argument('virtual_endpoint_name', options_list=['--name', '-n'], arg_type=virtual_endpoint_arg_type, validator=virtual_endpoint_name_validator)

        with self.argument_context('{} flexible-server virtual-endpoint delete'.format(command_group)) as c:
            c.argument('yes', arg_type=yes_arg_type)

        # long-term-retention
        for scope in ['show', 'start', 'pre-check']:
            argument_context_string = '{} flexible-server long-term-retention {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('backup_name', options_list=['--backup-name', '-b'], help='Long-term retention backup name.')

        with self.argument_context('{} flexible-server long-term-retention start'.format(command_group)) as c:
            c.argument('sas_url', options_list=['--sas-url', '-u'], help='Container SAS URL.')

        for scope in ['create', 'update']:
            argument_context_string = '{} flexible-server virtual-endpoint {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('endpoint_type', options_list=['--endpoint-type', '-t'], arg_type=endpoint_type_arg_type,
                           help='Virtual Endpoints offer two distinct types of connection points. Writer endpoint (Read/Write), this endpoint always points to the current primary server. Read-only endpoint, This endpoint can point to either a read replica or primary server. ')
                c.argument('members', options_list=['--members', '-m'], arg_type=members_type,
                           help='The read replicas the virtual endpoints point to. ')

        # replica
        with self.argument_context('{} flexible-server replica create'.format(command_group)) as c:
            c.argument('source_server', arg_type=source_server_arg_type)
            c.argument('replica_name', options_list=['--replica-name'],
                       help='The name of the read replica.')
            c.argument('name', options_list=['--name', '-n'],
                       help='The name of the read replica.')
            c.argument('zone', arg_type=zone_arg_type)
            c.argument('location', arg_type=get_location_type(self.cli_ctx))
            c.argument('vnet', arg_type=vnet_arg_type)
            c.argument('subnet', arg_type=subnet_arg_type)
            c.argument('private_dns_zone_arguments', private_dns_zone_arguments_arg_type)
            c.argument('vnet_address_prefix', arg_type=vnet_address_prefix_arg_type)
            c.argument('subnet_address_prefix', arg_type=subnet_address_prefix_arg_type)
            c.argument('byok_key', arg_type=key_arg_type)
            c.argument('byok_identity', arg_type=identity_arg_type)
            c.argument('tier', arg_type=tier_arg_type)
            c.argument('sku_name', arg_type=sku_name_arg_type)
            c.argument('storage_gb', arg_type=storage_gb_arg_type)
            c.argument('performance_tier', default=None, arg_type=performance_tier_arg_type)
            c.argument('yes', arg_type=yes_arg_type)
            c.argument('tags', arg_type=tags_type)

        with self.argument_context('{} flexible-server replica promote'.format(command_group)) as c:
            c.argument('replica_name', arg_type=replica_name_arg_type)
            c.argument('promote_mode', options_list=['--promote-mode'], required=False, arg_type=promote_mode_arg_type)
            c.argument('promote_option', options_list=['--promote-option'], required=False, arg_type=promote_option_arg_type)
            c.argument('yes', arg_type=yes_arg_type)

        # deploy
        with self.argument_context('{} flexible-server deploy setup'.format(command_group)) as c:
            c.argument('server_name', arg_type=server_name_resource_arg_type)
            c.argument('database_name', arg_type=database_name_arg_type)
            c.argument('administrator_login', arg_type=administrator_login_arg_type)
            c.argument('administrator_login_password', arg_type=administrator_login_password_arg_type)
            c.argument('sql_file_path', options_list=['--sql-file'], help='The path of the sql file. The sql file should be already in the repository')
            c.argument('action_name', options_list=['--action-name'], help='The name of the github action')
            c.argument('repository', options_list=['--repo'], help='The name of your github username and repository e.g., Azure/azure-cli ')
            c.argument('branch', options_list=['--branch'], help='The name of the branch you want upload github action file. The default will be your current branch.')
            c.argument('allow_push', default=False, options_list=['--allow-push'], arg_type=get_three_state_flag(), help='Push the action yml file to the remote repository. The changes will be pushed to origin repository, specified branch or current branch if not specified.')

        with self.argument_context('{} flexible-server deploy run'.format(command_group)) as c:
            c.argument('action_name', options_list=['--action-name'], help='The name of the github action')
            c.argument('branch', options_list=['--branch'], help='The name of the branch you want upload github action file. The default will be your current branch.')

        for scope in ['show', 'create', 'delete']:
            argument_context_string = '{} flexible-server backup {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('backup_name', id_part='child_name_1', options_list=['--backup-name', '-b'], help='The name of the backup.')

        with self.argument_context('{} flexible-server backup delete'.format(command_group)) as c:
            c.argument('yes', arg_type=yes_arg_type)

        # identity
        with self.argument_context('{} flexible-server identity'.format(command_group)) as c:
            c.argument('server_name', arg_type=server_name_resource_arg_type)

        for scope in ['assign', 'remove']:
            with self.argument_context('{} flexible-server identity'.format(command_group)) as c:
                c.argument('identities', arg_type=identities_arg_type)

        with self.argument_context('{} flexible-server identity show'.format(command_group)) as c:
            c.argument('identity', options_list=['--identity', '-n'], help='Name or ID of identity to show.', validator=validate_identity)

        with self.argument_context('{} flexible-server identity update'.format(command_group)) as c:
            c.argument('system_assigned', options_list=['--system-assigned'], arg_type=get_enum_type(['Enabled', 'Disabled']),
                       help='Enable or disable system assigned identity to authenticate to cloud services without storing credentials in code. Default is `Disabled`.')

        # fabric mirroring
        for scope in ['start', 'stop', 'update-databases']:
            with self.argument_context('{} flexible-server fabric-mirroring'.format(command_group)) as c:
                c.argument('server_name', arg_type=server_name_resource_arg_type)
                c.argument('yes', arg_type=yes_arg_type)

        for scope in ['start', 'update-databases']:
            with self.argument_context('{} flexible-server fabric-mirroring'.format(command_group)) as c:
                c.argument('database_names', options_list=['--database-names', '-d'], nargs='+',
                           help='Space-separated list of the database names to be mirrored. Required if --mirroring is enabled.')

        # microsoft-entra-admin
        with self.argument_context('{} flexible-server microsoft-entra-admin'.format(command_group)) as c:
            c.argument('server_name', arg_type=server_name_resource_arg_type)

        for scope in ['create', 'show', 'delete', 'wait']:
            with self.argument_context('{} flexible-server microsoft-entra-admin {}'.format(command_group, scope)) as c:
                c.argument('sid', options_list=['--object-id', '-i'], help='The unique ID of the Microsoft Entra administrator.')

        with self.argument_context('{} flexible-server microsoft-entra-admin create'.format(command_group)) as c:
            c.argument('login', options_list=['--display-name', '-u'], help='Display name of the Microsoft Entra administrator user or group.')
            c.argument('principal_type', options_list=['--type', '-t'], default='User', arg_type=get_enum_type(['User', 'Group', 'ServicePrincipal', 'Unknown']), help='Type of the Microsoft Entra administrator.')
            c.argument('identity', help='Name or ID of identity used for Microsoft Entra Authentication.', validator=validate_identity)

        # server advanced threat protection settings
        for scope in ['update', 'show']:
            argument_context_string = '{} flexible-server advanced-threat-protection-setting {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('server_name', arg_type=server_name_resource_arg_type)

        with self.argument_context('{} flexible-server advanced-threat-protection-setting update'.format(command_group)) as c:
            c.argument('state',
                       options_list=['--state'],
                       required=True,
                       help='State of advanced threat protection setting.',
                       arg_type=get_enum_type(['Enabled', 'Disabled']))

        # server log files
        for scope in ['download', 'list']:
            argument_context_string = '{} flexible-server server-logs {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('server_name', arg_type=server_name_resource_arg_type)

        with self.argument_context('{} flexible-server server-logs download'.format(command_group)) as c:
            c.argument('file_name', options_list=['--name', '-n'], nargs='+', help='Space-separated list of log filenames on the server to download.')

        with self.argument_context('{} flexible-server server-logs list'.format(command_group)) as c:
            c.argument('filename_contains', help='The pattern that file name should match.')
            c.argument('file_last_written', type=int, help='Integer in hours to indicate file last modify time.', default=72)
            c.argument('max_file_size', type=int, help='The file size limitation to filter files.')

        # private-endpoint-connection
        for scope in ['show', 'delete', 'approve', 'reject']:
            with self.argument_context('{} flexible-server private-endpoint-connection {}'.format(command_group, scope)) as c:
                c.argument('server_name', arg_type=server_name_resource_arg_type, required=False)
                c.argument('private_endpoint_connection_name', options_list=['--name', '-n'], required=False,
                           help='The name of the private endpoint connection associated with the Server. '
                           'Required if --id is not specified')
                c.extra('connection_id', options_list=['--id'], required=False,
                        help='The ID of the private endpoint connection associated with the Server. '
                        'If specified --server-name/-s and --name/-n, this should be omitted.')
                if scope == "approve" or scope == "reject":
                    c.argument('description', help='Comments for {} operation.'.format(scope), required=True)

        with self.argument_context('{} flexible-server private-endpoint-connection list'.format(command_group)) as c:
            c.argument('server_name', arg_type=server_name_resource_arg_type, required=False)

        # private-link-resource
        for scope in ['list', 'show']:
            with self.argument_context('{} flexible-server private-link-resource {}'.format(command_group, scope)) as c:
                c.argument('server_name', arg_type=server_name_resource_arg_type)

        # index tuning
        for scope in ['update', 'show', 'list-settings', 'show-settings', 'set-settings', 'list-recommendations']:
            argument_context_string = '{} flexible-server index-tuning {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('server_name', arg_type=server_name_resource_arg_type)

        with self.argument_context('{} flexible-server index-tuning update'.format(command_group)) as c:
            c.argument('index_tuning_enabled',
                       options_list=['--enabled'],
                       required=True,
                       help='Enable or disable index tuning feature.',
                       arg_type=get_enum_type(['True', 'False']))

        with self.argument_context('{} flexible-server index-tuning list-recommendations'.format(command_group)) as c:
            c.argument('recommendation_type',
                       options_list=['--recommendation-type', '-r'],
                       help='Retrieve recommendations based on type.',
                       arg_type=get_enum_type(['CreateIndex', 'DropIndex', 'ReIndex']))

            for scope in ['show-settings', 'set-settings']:
                argument_context_string = '{} flexible-server index-tuning {}'.format(command_group, scope)
                with self.argument_context(argument_context_string) as c:
                    c.argument('setting_name', options_list=['--name', '-n'], required=True,
                               arg_type=get_enum_type(get_autonomous_tuning_settings_map().keys()),
                               help='The name of the tuning setting.')

            with self.argument_context('{} flexible-server index-tuning set-settings'.format(command_group)) as c:
                c.argument('value', options_list=['--value', '-v'],
                           help='Value of the tuning setting.')

        # autonomous tuning
        for scope in ['update', 'show', 'list-settings', 'show-settings', 'set-settings', 'list-table-recommendations', 'list-index-recommendations']:
            argument_context_string = '{} flexible-server autonomous-tuning {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('server_name', arg_type=server_name_resource_arg_type)

        with self.argument_context('{} flexible-server autonomous-tuning update'.format(command_group)) as c:
            c.argument('autonomous_tuning_enabled',
                       options_list=['--enabled'],
                       required=True,
                       help='Enable or disable autonomous tuning feature.',
                       arg_type=get_enum_type(['True', 'False']))

        with self.argument_context('{} flexible-server autonomous-tuning list-index-recommendations'.format(command_group)) as c:
            c.argument('recommendation_type',
                       options_list=['--recommendation-type', '-r'],
                       help='Retrieve recommendations based on type.',
                       arg_type=get_enum_type(['CreateIndex', 'DropIndex', 'ReIndex']))

            with self.argument_context('{} flexible-server autonomous-tuning list-table-recommendations'.format(command_group)) as c:
                c.argument('recommendation_type',
                           options_list=['--recommendation-type', '-r'],
                           help='Retrieve recommendations based on type.',
                           arg_type=get_enum_type(['AnalyzeTable', 'VacuumTable']))

            for scope in ['show-settings', 'set-settings']:
                argument_context_string = '{} flexible-server autonomous-tuning {}'.format(command_group, scope)
                with self.argument_context(argument_context_string) as c:
                    c.argument('setting_name', options_list=['--name', '-n'], required=True,
                               arg_type=get_enum_type(get_autonomous_tuning_settings_map().keys()),
                               help='The name of the tuning setting.')

            with self.argument_context('{} flexible-server autonomous-tuning set-settings'.format(command_group)) as c:
                c.argument('value', options_list=['--value', '-v'],
                           help='Value of the tuning setting.')

        # migration
        handle_migration_parameters(command_group, server_name_arg_type, migration_id_arg_type)

    def handle_migration_parameters(command_group, server_name_arg_type, migration_id_arg_type):
        for scope in ['create', 'show', 'list', 'update', 'check-name-availability']:
            argument_context_string = '{} flexible-server migration {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('server_name', arg_type=server_name_arg_type, help='Migration target server name.')

                if scope == "create" or scope == "update" or scope == "show" or scope == "check-name-availability":
                    c.argument('migration_name', arg_type=migration_id_arg_type, options_list=['--migration-name'],
                               help='Name of the migration.')

                if scope == "create":
                    c.argument('properties', type=file_type, completer=FilesCompleter(), options_list=['--properties', '-b'],
                               help='Request properties. Use double or no quotes to pass in json filepath as argument.')
                    c.argument('migration_mode', arg_type=migration_id_arg_type, options_list=['--migration-mode'], required=False,
                               help='Either offline or online(with CDC) migration', choices=['offline', 'online'], default='offline')
                    c.argument('migration_option', arg_type=migration_id_arg_type, options_list=['--migration-option'], required=False,
                               help='Supported Migration Option. Default is ValidateAndMigrate.', choices=['Validate', 'ValidateAndMigrate', 'Migrate'], default='ValidateAndMigrate')
                    c.argument('tags', tags_type)
                    c.argument('location', arg_type=get_location_type(self.cli_ctx))
                elif scope == "list":
                    c.argument('migration_filter', options_list=['--filter'], required=False, choices=['Active', 'All'], default='Active',
                               help='Indicate whether all the migrations or just the Active migrations are returned. Valid values are: Active and All.')
                elif scope == "update":
                    c.argument('setup_logical_replication', options_list=['--setup-replication'], action='store_true', required=False,
                               help='Allow the migration workflow to setup logical replication on the source. Note that this command will restart the source server.')
                    c.argument('cutover', options_list=['--cutover'], required=False, action='store_true',
                               help='Cut-over the data migration for all the databases in the migration. After this is complete, subsequent updates to all databases will not be migrated to the target.')
                    c.argument('cancel', options_list=['--cancel'], required=False, action='store_true',
                               help='Cancel the data migration for all the databases.')

    _flexible_server_params('postgres')
