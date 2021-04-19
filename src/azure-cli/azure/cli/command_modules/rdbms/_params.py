# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (
    get_resource_name_completion_list,
    tags_type, get_location_type,
    get_enum_type,
    resource_group_name_type,
    get_three_state_flag)
from azure.cli.command_modules.rdbms.validators import configuration_value_validator, validate_subnet, \
    tls_validator, public_access_validator, maintenance_window_validator, ip_address_validator, retention_validator
from azure.cli.core.local_context import LocalContextAttribute, LocalContextAction

from .randomname.generate import generate_username
from ._flexible_server_util import get_current_time


def load_arguments(self, _):    # pylint: disable=too-many-statements

    server_completers = {
        'mariadb': get_resource_name_completion_list('Microsoft.DBForMariaDB/servers'),
        'mysql': get_resource_name_completion_list('Microsoft.DBForMySQL/servers'),
        'postgres': get_resource_name_completion_list('Microsoft.DBForPostgreSQL/servers')
    }

    def _complex_params(command_group):
        server_name_help = "Name of the server. The name can contain only lowercase letters, numbers, and the hyphen (-) character. " + \
                           "Minimum 3 characters and maximum 63 characters."
        server_name_scope = ['{}'.format(command_group)]
        server_name_setter_arg_type = CLIArgumentType(metavar='NAME', help=server_name_help, id_part='name',
                                                      local_context_attribute=LocalContextAttribute(name='server_name', actions=[LocalContextAction.SET], scopes=server_name_scope))
        server_name_getter_arg_type = CLIArgumentType(metavar='NAME', help=server_name_help, id_part='name',
                                                      local_context_attribute=LocalContextAttribute(name='server_name', actions=[LocalContextAction.GET], scopes=server_name_scope))
        server_name_arg_type = CLIArgumentType(metavar='NAME', help=server_name_help, id_part='name',
                                               local_context_attribute=LocalContextAttribute(name='server_name', actions=[LocalContextAction.SET, LocalContextAction.GET], scopes=server_name_scope))
        administrator_login_arg_type = CLIArgumentType(metavar='NAME',
                                                       local_context_attribute=LocalContextAttribute(name='administrator_login', actions=[LocalContextAction.GET, LocalContextAction.SET], scopes=server_name_scope))

        overriding_none_arg_type = CLIArgumentType(local_context_attribute=LocalContextAttribute(name='context_name', actions=[LocalContextAction.GET]))

        with self.argument_context(command_group) as c:
            c.argument('name', options_list=['--sku-name'], required=True)
            c.argument('server_name', arg_type=server_name_arg_type, completer=server_completers[command_group], options_list=['--server-name', '-s'])

        with self.argument_context('{} server'.format(command_group)) as c:
            c.ignore('family', 'capacity', 'tier')

            c.argument('server_name', arg_type=server_name_arg_type, options_list=['--name', '-n'], id_part='name', help='Name of the server. The name can contain only lowercase letters, numbers, and the hyphen (-) character. Minimum 3 characters and maximum 63 characters.')
            c.argument('administrator_login', options_list=['--admin-user', '-u'], help='Administrator username for the server. Once set, it cannot be changed.')
            c.argument('administrator_login_password', options_list=['--admin-password', '-p'], help='The password of the administrator. Minimum 8 characters and maximum 128 characters. Password must contain characters from three of the following categories: English uppercase letters, English lowercase letters, numbers, and non-alphanumeric characters.')
            c.argument('ssl_enforcement', arg_type=get_enum_type(['Enabled', 'Disabled']), options_list=['--ssl-enforcement'], help='Enable or disable ssl enforcement for connections to server. Default is Enabled.')
            c.argument('minimal_tls_version', arg_type=get_enum_type(['TLS1_0', 'TLS1_1', 'TLS1_2', 'TLSEnforcementDisabled']), options_list=['--minimal-tls-version'], help='Set the minimal TLS version for connections to server when SSL is enabled. Default is TLSEnforcementDisabled.', validator=tls_validator)
            c.argument('public_network_access', options_list=['--public-network-access', '--public'], help='Enable or disable public network access to server. When disabled, only connections made through Private Links can reach this server. Allowed values are : Enabled, Disabled, all, 0.0.0.0, <SingleIP>, <StartIP-DestinationIP>. Default is Enabled.')
            c.argument('tier', arg_type=get_enum_type(['Basic', 'GeneralPurpose', 'MemoryOptimized']), options_list=['--performance-tier'], help='The performance tier of the server.')
            c.argument('capacity', options_list=['--vcore'], type=int, help='Number of vcore.')
            c.argument('family', options_list=['--family'], arg_type=get_enum_type(['Gen4', 'Gen5']), help='Hardware generation.')
            c.argument('storage_mb', options_list=['--storage-size'], type=int, help='The storage capacity of the server (unit is megabytes). Minimum 5120 and increases in 1024 increments. Default is 51200.')
            c.argument('backup_retention', options_list=['--backup-retention'], type=int, help='The number of days a backup is retained. Range of 7 to 35 days. Default is 7 days.', validator=retention_validator)
            c.argument('auto_grow', arg_type=get_enum_type(['Enabled', 'Disabled']), options_list=['--auto-grow'], help='Enable or disable autogrow of the storage. Default value is Enabled.')
            c.argument('infrastructure_encryption', arg_type=get_enum_type(['Enabled', 'Disabled']), options_list=['--infrastructure-encryption', '-i'], help='Add an optional second layer of encryption for data using new encryption algorithm. Default value is Disabled.')
            c.argument('assign_identity', options_list=['--assign-identity'], help='Generate and assign an Azure Active Directory Identity for this server for use with key management services like Azure KeyVault.')
            c.argument('tags', tags_type)

            if command_group == 'mariadb':
                c.ignore('minimal_tls_version')
                c.ignore('assign_identity')
                c.ignore('infrastructure_encryption')

        with self.argument_context('{} server create'.format(command_group)) as c:
            c.argument('server_name', options_list=['--name', '-n'], arg_type=server_name_setter_arg_type)
            c.argument('sku_name', default='GP_Gen5_2', options_list=['--sku-name'],
                       help='The name of the sku. Follows the convention {pricing tier}_{compute generation}_{vCores} in shorthand. Examples: B_Gen5_1, GP_Gen5_4, MO_Gen5_16. ')
            c.argument('administrator_login', default=generate_username(), arg_group='Authentication')
            c.argument('administrator_login_password', arg_group='Authentication')

            c.argument('backup_retention', type=int, options_list=['--backup-retention'], help='The number of days a backup is retained. Range of 7 to 35 days. Default is 7 days.', validator=retention_validator)
            c.argument('geo_redundant_backup', arg_type=get_enum_type(['Enabled', 'Disabled']), options_list=['--geo-redundant-backup'], help='Enable or disable geo-redundant backups. Default value is Disabled. Not supported in Basic pricing tier.')
            c.argument('storage_mb', default=51200, options_list=['--storage-size'], type=int, help='The storage capacity of the server (unit is megabytes). Minimum 5120 and increases in 1024 increments. Default is 51200.')
            c.argument('auto_grow', arg_type=get_enum_type(['Enabled', 'Disabled']), options_list=['--auto-grow'], help='Enable or disable autogrow of the storage. Default value is Enabled.')
            c.argument('infrastructure_encryption', arg_type=get_enum_type(['Enabled', 'Disabled']), options_list=['--infrastructure-encryption', '-i'], help='Add an optional second layer of encryption for data using new encryption algorithm. Default value is Disabled.')
            c.argument('assign_identity', options_list=['--assign-identity'], help='Generate and assign an Azure Active Directory Identity for this server for use with key management services like Azure KeyVault.')

            c.argument('location', arg_type=get_location_type(self.cli_ctx))
            c.argument('version', help='Server major version.')

        with self.argument_context('{} server update'.format(command_group)) as c:
            c.ignore('family', 'capacity', 'tier')
            c.argument('sku_name', options_list=['--sku-name'], help='The name of the sku. Follows the convention {pricing tier}_{compute generation}_{vCores} in shorthand. Examples: B_Gen5_1, GP_Gen5_4, MO_Gen5_16.')
            c.argument('assign_identity', options_list=['--assign-identity'], help='Generate and assign an Azure Active Directory Identity for this server for use with key management services like Azure KeyVault.')

        with self.argument_context('{} server restore'. format(command_group)) as c:
            c.argument('server_name', options_list=['--name', '-n'], arg_type=overriding_none_arg_type)
            c.argument('source_server', options_list=['--source-server', '-s'], help='The name or resource ID of the source server to restore from.')
            c.argument('restore_point_in_time', options_list=['--restore-point-in-time', '--pitr-time'], help='The point in time in UTC to restore from (ISO8601 format), e.g., 2017-04-26T02:10:00+08:00')

        with self.argument_context('{} server georestore'. format(command_group)) as c:
            c.argument('location', arg_type=get_location_type(self.cli_ctx), required=True)
            c.argument('sku_name', options_list=['--sku-name'], required=False, help='The name of the sku. Defaults to sku of the source server. Follows the convention {pricing tier}_{compute generation}_{vCores} in shorthand. Examples: B_Gen5_1, GP_Gen5_4, MO_Gen5_16.')
            c.argument('source_server', options_list=['--source-server', '-s'], required=True, help='The name or ID of the source server to restore from.')
            c.argument('backup_retention', options_list=['--backup-retention'], type=int, help='The number of days a backup is retained. Range of 7 to 35 days. Default is 7 days.', validator=retention_validator)
            c.argument('geo_redundant_backup', options_list=['--geo-redundant-backup'], help='Enable or disable geo-redundant backups. Default value is Disabled. Not supported in Basic pricing tier.')

        with self.argument_context('{} server replica'.format(command_group)) as c:
            c.argument('server_name', options_list=['--name', '-n'], arg_type=overriding_none_arg_type)
            c.argument('source_server', options_list=['--source-server', '-s'], help='The name or resource ID of the master server to the create replica for.')
            c.argument('location', options_list=['--location', '-l'], help='Location. Values from: `az account list-locations`. If not provided, the create replica will be in the same location as the master server')
            c.argument('sku_name', options_list=['--sku-name'], help='The name of the sku. Follows the convention {pricing tier}_{compute generation}_{vCores} in shorthand. Examples: B_Gen5_1, GP_Gen5_4, MO_Gen5_16.')

        with self.argument_context('{} server configuration set'.format(command_group)) as c:
            c.argument('value', help='Value of the configuration. If not provided, configuration value will be set to default.', validator=configuration_value_validator)
            c.argument('configuration_name', options_list=['--name', '-n'], id_part='child_name_1', help='The name of the configuration')
            c.ignore('source')

        with self.argument_context('{} server wait'.format(command_group)) as c:
            c.ignore('created', 'deleted', 'updated')

        with self.argument_context('{} server delete'.format(command_group)) as c:
            c.argument('server_name', options_list=['--name', '-n'], arg_type=server_name_getter_arg_type)

        with self.argument_context('{} server-logs'.format(command_group)) as c:
            c.argument('file_name', options_list=['--name', '-n'], nargs='+', help='Space-separated list of log filenames on the server to download.')
            c.argument('max_file_size', type=int, help='The file size limitation to filter files.')
            c.argument('file_last_written', type=int, help='Integer in hours to indicate file last modify time, default value is 72.')
            c.argument('filename_contains', help='The pattern that file name should match.')

        with self.argument_context('{} server-logs list'.format(command_group)) as c:
            c.argument('server_name', id_part=None, help='Name of the Server.')

        with self.argument_context('{} db'.format(command_group)) as c:
            c.argument('database_name', options_list=['--name', '-n'], help='The name of the database')
            c.argument('charset', options_list=['--charset'], help='The charset of the database')
            c.argument('collation', options_list=['--collation'], help='The collation of the database')

        with self.argument_context('{} db list'.format(command_group)) as c:
            c.argument('server_name', id_part=None, help='Name of the Server.')

        with self.argument_context('{} server firewall-rule'.format(command_group)) as c:
            c.argument('server_name', options_list=['--server-name', '-s'])
            c.argument('firewall_rule_name', options_list=['--name', '-n'], id_part='child_name_1', help='The name of the firewall rule. The firewall rule name cannot be empty. The firewall rule name can only contain 0-9, a-z, A-Z, \'-\' and \'_\'. Additionally, the firewall rule name cannot exceed 128 characters.')
            c.argument('start_ip_address', options_list=['--start-ip-address'], help='The start IP address of the firewall rule. Must be IPv4 format. Use value \'0.0.0.0\' to represent all Azure-internal IP addresses.')
            c.argument('end_ip_address', options_list=['--end-ip-address'], help='The end IP address of the firewall rule. Must be IPv4 format. Use value \'0.0.0.0\' to represent all Azure-internal IP addresses.')

        with self.argument_context('{} server vnet-rule'.format(command_group)) as c:
            c.argument('server_name', options_list=['--server-name', '-s'])
            c.argument('virtual_network_rule_name', options_list=['--name', '-n'], id_part='child_name_1', help='The name of the vnet rule.')
            c.argument('virtual_network_subnet_id', options_list=['--subnet'], help='Name or ID of the subnet that allows access to an Azure Postgres Server. If subnet name is provided, --vnet-name must be provided.')
            c.argument('ignore_missing_vnet_service_endpoint', options_list=['--ignore-missing-endpoint', '-i'], help='Create vnet rule before virtual network has vnet service endpoint enabled', arg_type=get_three_state_flag())

        with self.argument_context('{} server vnet-rule create'.format(command_group)) as c:
            c.extra('vnet_name', options_list=['--vnet-name'], help='The virtual network name', validator=validate_subnet)

        with self.argument_context('{} server vnet-rule update'.format(command_group)) as c:
            c.extra('vnet_name', options_list=['--vnet-name'], help='The virtual network name',
                    validator=validate_subnet)

        with self.argument_context('{} server configuration'.format(command_group)) as c:
            c.argument('server_name', options_list=['--server-name', '-s'])
            c.argument('configuration_name', options_list=['--name', '-n'], id_part='child_name_1')

        with self.argument_context('{} server replica list'.format(command_group)) as c:
            c.argument('server_name', options_list=['--server-name', '-s'], help='Name of the master server.')

        for item in ['approve', 'reject', 'delete', 'show']:
            with self.argument_context('{} server private-endpoint-connection {}'.format(command_group, item)) as c:
                c.argument('private_endpoint_connection_name', options_list=['--name', '-n'], required=False,
                           help='The name of the private endpoint connection associated with the Server. '
                                'Required if --id is not specified')
                c.extra('connection_id', options_list=['--id'], required=False,
                        help='The ID of the private endpoint connection associated with the Server. '
                             'If specified --server-name/-s and --name/-n, this should be omitted.')
                c.argument('server_name', options_list=['--server-name', '-s'], required=False,
                           help='Name of the Server. Required if --id is not specified')
                c.argument('resource_group_name', help='The resource group name of specified server.',
                           required=False)
                c.argument('description', help='Comments for {} operation.'.format(item))

        with self.argument_context('{} server private-link-resource'.format(command_group)) as c:
            c.argument('server_name', options_list=['--server-name', '-s'], required=True, help='Name of the Server.')

        with self.argument_context('{} server list-skus'.format(command_group)) as c:
            c.argument('location_name', options_list=['--location', '-l'])

        with self.argument_context('{} server show-connection-string'.format(command_group)) as c:
            c.argument('server_name', options_list=['--server-name', '-s'], arg_type=server_name_arg_type, help='Name of the server.')
            c.argument('administrator_login', options_list=['--admin-user', '-u'], arg_type=administrator_login_arg_type,
                       help='The login username of the administrator.')
            c.argument('administrator_login_password', options_list=['--admin-password', '-p'],
                       help='The login password of the administrator.')
            c.argument('database_name', options_list=['--database-name', '-d'], help='The name of a database.')

        if command_group != 'mariadb':
            with self.argument_context('{} server key'.format(command_group)) as c:
                c.argument('server_name', options_list=['--name', '-s'])
                c.argument('kid', options_list=['--kid', '-k'], help='The Azure Key Vault key identifier of the server key. An example key identifier is "https://YourVaultName.vault.azure.net/keys/YourKeyName/01234567890123456789012345678901"')

            with self.argument_context('{} server ad-admin'.format(command_group)) as c:
                c.argument('server_name', options_list=['--server-name', '-s'])
                c.argument('login', options_list=['--display-name', '-u'], help='Display name of the Azure AD administrator user or group.')
                c.argument('sid', options_list=['--object-id', '-i'], help='The unique ID of the Azure AD administrator.')

        if command_group == 'mysql':
            with self.argument_context('{} server upgrade'.format(command_group)) as c:
                c.argument('target_server_version', options_list=['--target-server-version', '-t'], required=True, help='The server version you want to upgrade your mysql server to, currently only support 5.7.')

    _complex_params('mariadb')
    _complex_params('mysql')
    _complex_params('postgres')

    # Flexible-server
    def _flexible_server_params(command_group):

        server_name_setter_arg_type = CLIArgumentType(metavar='NAME',
                                                      help="Name of the server. The name can contain only lowercase letters, numbers, and the hyphen (-) character. Minimum 3 characters and maximum 63 characters.",
                                                      local_context_attribute=LocalContextAttribute(name='server_name', actions=[LocalContextAction.SET], scopes=['{} flexible-server'.format(command_group)]))

        server_name_getter_arg_type = CLIArgumentType(metavar='NAME',
                                                      help="Name of the server. The name can contain only lowercase letters, numbers, and the hyphen (-) character. Minimum 3 characters and maximum 63 characters.",
                                                      local_context_attribute=LocalContextAttribute(name='server_name', actions=[LocalContextAction.GET], scopes=['{} flexible-server'.format(command_group)]))

        server_name_arg_type = CLIArgumentType(metavar='NAME',
                                               help="Name of the server. The name can contain only lowercase letters, numbers, and the hyphen (-) character. Minimum 3 characters and maximum 63 characters.",
                                               local_context_attribute=LocalContextAttribute(name='server_name', actions=[LocalContextAction.SET, LocalContextAction.GET], scopes=['{} flexible-server'.format(command_group)]))

        administrator_login_setter_arg_type = CLIArgumentType(metavar='NAME',
                                                              local_context_attribute=LocalContextAttribute(name='administrator_login', actions=[LocalContextAction.SET], scopes=['{} flexible-server'.format(command_group)]))

        administrator_login_arg_type = CLIArgumentType(metavar='NAME',
                                                       local_context_attribute=LocalContextAttribute(name='administrator_login', actions=[LocalContextAction.GET, LocalContextAction.SET], scopes=['{} flexible-server'.format(command_group)]))

        database_name_setter_arg_type = CLIArgumentType(metavar='NAME',
                                                        local_context_attribute=LocalContextAttribute(name='database_name', actions=[LocalContextAction.SET], scopes=['{} flexible-server'.format(command_group)]))

        database_name_getter_arg_type = CLIArgumentType(metavar='NAME',
                                                        local_context_attribute=LocalContextAttribute(name='database_name', actions=[LocalContextAction.GET], scopes=['{} flexible-server'.format(command_group)]))

        database_name_arg_type = CLIArgumentType(metavar='NAME',
                                                 local_context_attribute=LocalContextAttribute(name='database_name', actions=[LocalContextAction.GET, LocalContextAction.SET], scopes=['{} flexible-server'.format(command_group)]))

        overriding_none_arg_type = CLIArgumentType(local_context_attribute=LocalContextAttribute(name='context_name', actions=[LocalContextAction.GET]))

        with self.argument_context('{} flexible-server'.format(command_group)) as c:
            c.argument('server_name', id_part='name', options_list=['--name', '-n'], arg_type=server_name_arg_type)

        with self.argument_context('{} flexible-server create'.format(command_group)) as c:
            # Add create mode as a parameter
            if command_group == 'postgres':
                c.argument('tier', default='GeneralPurpose', options_list=['--tier'],
                           help='Compute tier of the server. Accepted values: Burstable, GeneralPurpose, Memory Optimized ')
                c.argument('sku_name', default='Standard_D2s_v3', options_list=['--sku-name'],
                           help='The name of the compute SKU. Follows the convention Standard_{VM name}. Examples: Standard_D4s_v3 ')
                c.argument('storage_mb', default='128', options_list=['--storage-size'], type=int,
                           help='The storage capacity of the server. Minimum is 32 GiB and max is 16 TiB.')
                c.argument('backup_retention', default=7, type=int, options_list=['--backup-retention'],
                           help='The number of days a backup is retained. Range of 7 to 35 days. Default is 7 days.',
                           validator=retention_validator)
                c.argument('version', default='12', options_list=['--version'],
                           help='Server major version.')
                c.argument('zone', options_list=['--zone', '-z'],
                           help='Availability zone into which to provision the resource.')
            elif command_group == 'mysql':
                c.argument('tier', default='Burstable',
                           help='Compute tier of the server. Accepted values: Burstable, GeneralPurpose, Memory Optimized ')
                c.argument('sku_name', default='Standard_B1ms', options_list=['--sku-name'],
                           help='The name of the compute SKU. Follows the convention Standard_{VM name}. Examples: Standard_B1ms, Standard_E16ds_v4 ')
                c.argument('storage_mb', default='10', options_list=['--storage-size'], type=int,
                           help='The storage capacity of the server. Minimum is 5 GiB and increases in 1 GiB increments. Max is 16 TiB.')
                c.argument('backup_retention', default=7, type=int, options_list=['--backup-retention'],
                           help='The number of days a backup is retained. Range of 7 to 35 days. Default is 7 days.')
                c.argument('version', default='5.7', options_list=['--version'],
                           help='Server major version.')
                c.argument('zone', options_list=['--zone', '-z'],
                           help='Availability zone into which to provision the resource.')
                c.argument('iops', type=int, options_list=['--iops'],
                           help='Number of IOPS to be allocated for this server. You will get certain amount of free IOPS based '
                                'on compute and storage provisioned. The default value for IOPS is free IOPS. '
                                'To learn more about IOPS based on compute and storage, refer to IOPS in Azure Database for MySQL Flexible Server')

            c.argument('vnet_resource_id', options_list=['--vnet'], help='Name of an existing virtual network or name of a new one to create. The name must be between 2 to 64 characters. The name must begin with a letter or number, end with a letter, number or underscore, and may contain only letters, numbers, underscores, periods, or hyphens.')
            c.argument('vnet_address_prefix', options_list=['--address-prefixes'], help='The IP address prefix to use when creating a new virtual network in CIDR format. Default value is 10.0.0.0/16.')
            c.argument('subnet_address_prefix', options_list=['--subnet-prefixes'], help='The subnet IP address prefix to use when creating a new VNet in CIDR format. Default value is 10.0.0.0/24.')
            c.argument('subnet_arm_resource_id', options_list=['--subnet'],
                       help='Resource ID of an existing subnet. Please note that the subnet will be delegated to Microsoft.DBforPostgreSQL/flexibleServers/Microsoft.DBforMySQL/flexibleServers.After delegation, this subnet cannot be used for any other type of Azure resources.')
            c.argument('server_name', options_list=['--name', '-n'], arg_type=server_name_setter_arg_type)
            c.argument('location', arg_type=get_location_type(self.cli_ctx))
            c.argument('administrator_login', default=generate_username(), options_list=['--admin-user', '-u'], arg_group='Authentication', arg_type=administrator_login_setter_arg_type,
                       help='Administrator username for the server. Once set, it cannot be changed. ')
            c.argument('administrator_login_password', options_list=['--admin-password', '-p'],
                       help='The password of the administrator. Minimum 8 characters and maximum 128 characters. Password must contain characters from three of the following categories: English uppercase letters, English lowercase letters, numbers, and non-alphanumeric characters.',
                       arg_group='Authentication')
            c.argument('tags', tags_type)
            c.argument('public_access', options_list=['--public-access'],
                       help='Determines the public access. Enter single or range of IP addresses to be included in the allowed list of IPs. IP address ranges must be dash-separated and not contain any spaces. Specifying 0.0.0.0 allows public access from any resources deployed within Azure to access your server. Setting it to "None" sets the server in public access mode but does not create a firewall rule. ',
                       validator=public_access_validator)
            c.argument('high_availability', default="Disabled", options_list=['--high-availability'], help='Enable or disable high availability feature.  Default value is Disabled.')
            c.argument('assign_identity', options_list=['--assign-identity'],
                       help='Generate and assign an Azure Active Directory Identity for this server for use with key management services like Azure KeyVault. No need to enter extra argument.')
            c.ignore('database_name')

        with self.argument_context('{} flexible-server delete'.format(command_group)) as c:
            c.argument('resource_group_name', required=True)
            c.argument('server_name', id_part='name', options_list=['--name', '-n'], required=True, arg_type=server_name_getter_arg_type)
            c.argument('yes', options_list=['--yes', '-y'], action='store_true',
                       help='Do not prompt for confirmation.')

        with self.argument_context('{} flexible-server restore'.format(command_group)) as c:
            c.argument('server_name', options_list=['--name', '-n'], arg_type=overriding_none_arg_type,
                       help='The name of the new server that is created by the restore command.')
            c.argument('restore_point_in_time', options_list=['--restore-time'], default=get_current_time(),
                       help='The point in time in UTC to restore from (ISO8601 format), e.g., 2017-04-26T02:10:00+00:00')
            if command_group == 'postgres':
                c.argument('source_server', options_list=['--source-server'],
                           help='The name of the source server to restore from.')
                c.argument('zone', options_list=['--zone'],
                           help='Availability zone into which to provision the resource.')
            elif command_group == 'mysql':
                c.argument('source_server', options_list=['--source-server'],
                           help='The name or resource ID of the source server to restore from.')

        with self.argument_context('{} flexible-server update'.format(command_group)) as c:
            c.ignore('assign_identity')
            c.argument('administrator_login_password', options_list=['--admin-password', '-p'],
                       help='The password of the administrator. Minimum 8 characters and maximum 128 characters. Password must contain characters from three of the following categories: English uppercase letters, English lowercase letters, numbers, and non-alphanumeric characters.',)
            c.argument('ha_enabled', options_list=['--high-availability'], arg_type=get_enum_type(['Enabled', 'Disabled']),
                       help='Enable or disable high availability feature.  Default value is Disabled.')
            c.argument('maintenance_window', options_list=['--maintenance-window'], validator=maintenance_window_validator,
                       help='Period of time (UTC) designated for maintenance. Examples: "Sun:23:30" to schedule on Sunday, 11:30pm UTC. To set back to default pass in "Disabled".')
            c.argument('tags', tags_type)
            if command_group == 'mysql':
                c.argument('tier', options_list=['--tier'],
                           help='Compute tier of the server. Accepted values: Burstable, GeneralPurpose, Memory Optimized')
                c.argument('sku_name', options_list=['--sku-name'],
                           help='The name of the compute SKU. Follows the convention Standard_{VM name}. Examples: Standard_B1ms, Standard_E16ds_v4 ')
                c.argument('storage_mb', options_list=['--storage-size'], type=int,
                           help='The storage capacity of the server. Minimum is 5 GiB and increases in 1 GiB increments. Max is 16 TiB.')
                c.argument('backup_retention', type=int, options_list=['--backup-retention'],
                           help='The number of days a backup is retained. Range of 7 to 35 days. Default is 7 days.')
                c.argument('auto_grow', arg_type=get_enum_type(['Enabled', 'Disabled']), options_list=['--storage-auto-grow'],
                           help='Enable or disable autogrow of the storage. Default value is Enabled.')
                c.argument('ssl_enforcement', arg_type=get_enum_type(['Enabled', 'Disabled']),
                           options_list=['--ssl-enforcement'],
                           help='Enable or disable ssl enforcement for connections to server. Default is Enabled.')
                c.argument('subnet_arm_resource_id', options_list=['--subnet'],
                           help='Name or ID of the subnet that allows access to an Azure Flexible Server MySQL Server. ')
                c.argument('replication_role', options_list=['--replication-role'],
                           help='The replication role of the server.')
                c.argument('iops', type=int, options_list=['--iops'],
                           help='Number of IOPS to be allocated for this server. You will get certain amount of free IOPS based '
                                'on compute and storage provisioned. The default value for IOPS is free IOPS. '
                                'To learn more about IOPS based on compute and storage, refer to IOPS in Azure Database for MySQL Flexible Server')
            elif command_group == 'postgres':
                c.argument('tier', options_list=['--tier'],
                           help='Compute tier of the server. Accepted values: Burstable, GeneralPurpose, Memory Optimized')
                c.argument('sku_name', options_list=['--sku-name'],
                           help='The name of the compute SKU. Follows the convention Standard_{VM name}. Examples: Standard_D4s_v3 ')
                c.argument('storage_mb', options_list=['--storage-size'], type=int,
                           help='The storage capacity of the server. Minimum is 32 GiB and max is 16 TiB.')
                c.argument('backup_retention', type=int, options_list=['--backup-retention'],
                           help='The number of days a backup is retained. Range of 7 to 35 days. Default is 7 days.', validator=retention_validator)

        with self.argument_context('{} flexible-server list-skus'.format(command_group)) as c:
            c.argument('location', arg_type=get_location_type(self.cli_ctx))

        # flexible-server parameter
        for scope in ['list', 'set', 'show']:
            argument_context_string = '{} flexible-server parameter {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                if scope == "list":
                    c.argument('server_name', id_part=None, options_list=['--server-name', '-s'], arg_type=server_name_arg_type)
                else:
                    c.argument('server_name', id_part='name', options_list=['--server-name', '-s'],
                               arg_type=server_name_arg_type)

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
        for scope in ['create', 'delete', 'list', 'show', 'update']:
            argument_context_string = '{} flexible-server firewall-rule {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('resource_group_name', arg_type=resource_group_name_type)
                if scope == "list":
                    c.argument('server_name', id_part=None, options_list=['--name', '-n'], arg_type=server_name_arg_type)
                else:
                    c.argument('server_name', id_part='name', options_list=['--name', '-n'], arg_type=server_name_arg_type)

        for scope in ['create', 'delete', 'show', 'update']:
            argument_context_string = '{} flexible-server firewall-rule {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('firewall_rule_name', id_part='child_name_1', options_list=['--rule-name', '-r'],
                           help='The name of the firewall rule. If name is omitted, default name will be chosen for firewall name. The firewall rule name can only contain 0-9, a-z, A-Z, \'-\' and \'_\'. Additionally, the firewall rule name cannot exceed 128 characters. ')

        with self.argument_context('{} flexible-server firewall-rule create'.format(command_group)) as c:
            c.argument('end_ip_address', options_list=['--end-ip-address'], validator=ip_address_validator,
                       help='The end IP address of the firewall rule. Must be IPv4 format. Use value \'0.0.0.0\' to represent all Azure-internal IP addresses. ')
            c.argument('start_ip_address', options_list=['--start-ip-address'], validator=ip_address_validator,
                       help='The start IP address of the firewall rule. Must be IPv4 format. Use value \'0.0.0.0\' to represent all Azure-internal IP addresses. ')

        with self.argument_context('{} flexible-server firewall-rule delete'.format(command_group)) as c:
            c.argument('yes', options_list=['--yes', '-y'], action='store_true', help='Do not prompt for confirmation.')

        with self.argument_context('{} flexible-server firewall-rule update'.format(command_group)) as c:
            c.argument('end_ip_address', options_list=['--end-ip-address'], validator=ip_address_validator,
                       help='When using \'set\' or \'add\', preserve string literals instead of attempting to convert to JSON.')
            c.argument('start_ip_address', options_list=['--start-ip-address'], validator=ip_address_validator,
                       help='The start IP address of the firewall rule. Must be IPv4 format. Use value \'0.0.0.0\' to represent all Azure-internal IP addresses. ')

        # db
        for scope in ['create', 'delete', 'list', 'show']:
            argument_context_string = '{} flexible-server db {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('resource_group_name', arg_type=resource_group_name_type)
                c.argument('server_name', id_part='name', options_list=['--server-name', '-s'], arg_type=server_name_arg_type)
                c.argument('database_name', id_part='child_name_1', arg_type=database_name_arg_type, options_list=['--database-name', '-d'], help='The name of a database.')

        with self.argument_context('{} flexible-server db list'.format(command_group)) as c:
            c.argument('server_name', id_part=None, options_list=['--server-name', '-s'], arg_type=server_name_arg_type)
            c.argument('database_name', id_part=None, arg_type=database_name_arg_type, options_list=['--database-name', '-d'], help='The name of the database.')

        with self.argument_context('{} flexible-server db create'.format(command_group)) as c:
            c.argument('database_name', id_part='child_name_1', arg_type=database_name_setter_arg_type, options_list=['--database-name', '-d'], help='The name of a database.')
            c.argument('charset', help='The charset of the database. The default value is UTF8')
            c.argument('collation', help='The collation of the database.')

        with self.argument_context('{} flexible-server db delete'.format(command_group)) as c:
            c.argument('database_name', id_part='child_name_1', arg_type=database_name_getter_arg_type, options_list=['--database-name', '-d'], help='The name of a database.')
            c.argument('yes', options_list=['--yes', '-y'], action='store_true', help='Do not prompt for confirmation.')

        with self.argument_context('{} flexible-server show-connection-string'.format(command_group)) as c:
            c.argument('server_name', options_list=['--server-name', '-s'], arg_type=server_name_arg_type, help='Name of the server.')
            c.argument('administrator_login', arg_type=administrator_login_arg_type, options_list=['--admin-user', '-u'],
                       help='The login username of the administrator.')
            c.argument('administrator_login_password', options_list=['--admin-password', '-p'],
                       help='The login password of the administrator.')
            c.argument('database_name', arg_type=database_name_arg_type, options_list=['--database-name', '-d'], help='The name of the database.')

        with self.argument_context('{} flexible-server replica list'.format(command_group)) as c:
            c.argument('server_name', id_part=None, options_list=['--name', '-n'], help='Name of the source server.')

        with self.argument_context('{} flexible-server replica create'.format(command_group)) as c:
            c.argument('server_name', options_list=['--source-server'],
                       help='The name or resource ID of the source server to restore from.')
            c.argument('replica_name', options_list=['--replica-name'],
                       help='The name of the server to restore to.')
            c.ignore('location')
            c.ignore('sku_name')
            c.ignore('tier')

        with self.argument_context('{} flexible-server replica stop-replication'.format(command_group)) as c:
            c.argument('server_name', options_list=['--name', '-n'], help='Name of the replica server.')

    _flexible_server_params('postgres')
    _flexible_server_params('mysql')
