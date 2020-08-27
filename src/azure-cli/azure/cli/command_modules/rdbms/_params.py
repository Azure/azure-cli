# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (
    get_resource_name_completion_list,
    tags_type, get_location_type,
    get_enum_type,
    get_three_state_flag)
from azure.cli.command_modules.rdbms.validators import configuration_value_validator, validate_subnet, retention_validator, tls_validator
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from .randomname.generate import generate_username
from azure.cli.core.local_context import LocalContextAttribute, LocalContextAction
from azure.cli.core.commands.parameters import (resource_group_name_type, get_location_type,
                                                get_resource_name_completion_list)
from ._util import create_random_resource_name

def load_arguments(self, _):    # pylint: disable=too-many-statements

    server_completers = {
        'mariadb': get_resource_name_completion_list('Microsoft.DBForMariaDB/servers'),
        'mysql': get_resource_name_completion_list('Microsoft.DBForMySQL/servers'),
        'postgres': get_resource_name_completion_list('Microsoft.DBForPostgreSQL/servers')
    }

    def _complex_params(command_group):
        with self.argument_context('{} server create'.format(command_group)) as c:
            c.argument('sku_name', options_list=['--sku-name'], required=True, help='The name of the sku. Follows the convention {pricing tier}_{compute generation}_{vCores} in shorthand. Examples: B_Gen5_1, GP_Gen5_4, MO_Gen5_16. ')
            c.argument('administrator_login', required=True, arg_group='Authentication')
            c.argument('administrator_login_password', required=True, arg_group='Authentication')

            c.argument('backup_retention', type=int, options_list=['--backup-retention'], help='The number of days a backup is retained. Range of 7 to 35 days. Default is 7 days.', validator=retention_validator)
            c.argument('geo_redundant_backup', arg_type=get_enum_type(['Enabled', 'Disabled']), options_list=['--geo-redundant-backup'], help='Enable or disable geo-redundant backups. Default value is Disabled. Not supported in Basic pricing tier.')
            c.argument('storage_mb', options_list=['--storage-size'], type=int, help='The storage capacity of the server (unit is megabytes). Minimum 5120 and increases in 1024 increments. Default is 51200.')
            c.argument('auto_grow', arg_type=get_enum_type(['Enabled', 'Disabled']), options_list=['--auto-grow'], help='Enable or disable autogrow of the storage. Default value is Enabled.')
            c.argument('infrastructure_encryption', arg_type=get_enum_type(['Enabled', 'Disabled']), options_list=['--infrastructure-encryption', '-i'], help='Add an optional second layer of encryption for data using new encryption algorithm. Default value is Disabled.')
            c.argument('assign_identity', options_list=['--assign-identity'], help='Generate and assign an Azure Active Directory Identity for this server for use with key management services like Azure KeyVault.')

            c.argument('location', arg_type=get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
            c.argument('version', help='Server major version.')

        with self.argument_context('{} server update'.format(command_group)) as c:
            c.ignore('family', 'capacity', 'tier')
            c.argument('sku_name', options_list=['--sku-name'], help='The name of the sku. Follows the convention {pricing tier}_{compute generation}_{vCores} in shorthand. Examples: B_Gen5_1, GP_Gen5_4, MO_Gen5_16.')
            c.argument('assign_identity', options_list=['--assign-identity'], help='Generate and assign an Azure Active Directory Identity for this server for use with key management services like Azure KeyVault.')

        with self.argument_context('{} server restore'. format(command_group)) as c:
            c.argument('source_server', options_list=['--source-server', '-s'], help='The name or resource ID of the source server to restore from.')
            c.argument('restore_point_in_time', help='The point in time to restore from (ISO8601 format), e.g., 2017-04-26T02:10:00+08:00')

        with self.argument_context('{} server georestore'. format(command_group)) as c:
            c.argument('location', arg_type=get_location_type(self.cli_ctx), required=True)
            c.argument('sku_name', options_list=['--sku-name'], required=False, help='The name of the sku. Defaults to sku of the source server. Follows the convention {pricing tier}_{compute generation}_{vCores} in shorthand. Examples: B_Gen5_1, GP_Gen5_4, MO_Gen5_16.')
            c.argument('source_server', options_list=['--source-server', '-s'], required=True, help='The name or ID of the source server to restore from.')
            c.argument('backup_retention', options_list=['--backup-retention'], type=int, help='The number of days a backup is retained. Range of 7 to 35 days. Default is 7 days.', validator=retention_validator)
            c.argument('geo_redundant_backup', options_list=['--geo-redundant-backup'], help='Enable or disable geo-redundant backups. Default value is Disabled. Not supported in Basic pricing tier.')

        with self.argument_context('{} server replica'.format(command_group)) as c:
            c.argument('source_server', options_list=['--source-server', '-s'], help='The name or resource ID of the master server to the create replica for.')
            c.argument('location', options_list=['--location', '-l'], help='Location. Values from: `az account list-locations`. If not provided, the create replica will be in the same location as the master server')
            c.argument('sku_name', options_list=['--sku-name'], help='The name of the sku. Follows the convention {pricing tier}_{compute generation}_{vCores} in shorthand. Examples: B_Gen5_1, GP_Gen5_4, MO_Gen5_16.')

        with self.argument_context('{} server configuration set'.format(command_group)) as c:
            c.argument('value', help='Value of the configuration. If not provided, configuration value will be set to default.', validator=configuration_value_validator)
            c.ignore('source')

        with self.argument_context('{} server wait'.format(command_group)) as c:
            c.ignore('created', 'deleted', 'updated')

    _complex_params('mariadb')
    _complex_params('mysql')
    _complex_params('postgres')

    for scope in ['mariadb', 'mysql', 'postgres']:
        with self.argument_context(scope) as c:
            c.argument('name', options_list=['--sku-name'], required=True)
            c.argument('server_name', completer=server_completers[scope], options_list=['--server-name', '-s'], help='Name of the server. The name can contain only lowercase letters, numbers, and the hyphen (-) character. Minimum 3 characters and maximum 63 characters.')

    for scope in ['mariadb server', 'mysql server', 'postgres server']:
        with self.argument_context(scope) as c:
            c.ignore('family', 'capacity', 'tier')

            c.argument('server_name', options_list=['--name', '-n'], id_part='name', help='Name of the server. The name can contain only lowercase letters, numbers, and the hyphen (-) character. Minimum 3 characters and maximum 63 characters.')
            c.argument('administrator_login', options_list=['--admin-user', '-u'], help='Administrator username for the server. Once set, it cannot be changed.')
            c.argument('administrator_login_password', options_list=['--admin-password', '-p'], help='The password of the administrator. Minimum 8 characters and maximum 128 characters. Password must contain characters from three of the following categories: English uppercase letters, English lowercase letters, numbers, and non-alphanumeric characters.')
            c.argument('ssl_enforcement', arg_type=get_enum_type(['Enabled', 'Disabled']), options_list=['--ssl-enforcement'], help='Enable or disable ssl enforcement for connections to server. Default is Enabled.')
            c.argument('minimal_tls_version', arg_type=get_enum_type(['TLS1_0', 'TLS1_1', 'TLS1_2', 'TLSEnforcementDisabled']), options_list=['--minimal-tls-version'], help='Set the minimal TLS version for connections to server when SSL is enabled. Default is TLSEnforcementDisabled.', validator=tls_validator)
            c.argument('public_network_access', arg_type=get_enum_type(['Enabled', 'Disabled']), options_list=['--public-network-access'], help='Enable or disable public network access to server. When disabled, only connections made through Private Links can reach this server. Default is Enabled.')
            c.argument('tier', arg_type=get_enum_type(['Basic', 'GeneralPurpose', 'MemoryOptimized']), options_list=['--performance-tier'], help='The performance tier of the server.')
            c.argument('capacity', options_list=['--vcore'], type=int, help='Number of vcore.')
            c.argument('family', options_list=['--family'], arg_type=get_enum_type(['Gen4', 'Gen5']), help='Hardware generation.')
            c.argument('storage_mb', options_list=['--storage-size'], type=int, help='The storage capacity of the server (unit is megabytes). Minimum 5120 and increases in 1024 increments. Default is 51200.')
            c.argument('backup_retention', options_list=['--backup-retention'], type=int, help='The number of days a backup is retained. Range of 7 to 35 days. Default is 7 days.', validator=retention_validator)
            c.argument('auto_grow', arg_type=get_enum_type(['Enabled', 'Disabled']), options_list=['--auto-grow'], help='Enable or disable autogrow of the storage. Default value is Enabled.')
            c.argument('infrastructure_encryption', arg_type=get_enum_type(['Enabled', 'Disabled']), options_list=['--infrastructure-encryption', '-i'], help='Add an optional second layer of encryption for data using new encryption algorithm. Default value is Disabled.')
            c.argument('assign_identity', options_list=['--assign-identity'], help='Generate and assign an Azure Active Directory Identity for this server for use with key management services like Azure KeyVault.')
            c.argument('tags', tags_type)

            if scope == 'mariadb server':
                c.ignore('minimal_tls_version')
                c.ignore('assign_identity')
                c.ignore('infrastructure_encryption')

    for scope in ['mariadb server-logs', 'mysql server-logs', 'postgres server-logs']:
        with self.argument_context(scope) as c:
            c.argument('file_name', options_list=['--name', '-n'], nargs='+', help='Space-separated list of log filenames on the server to download.')
            c.argument('max_file_size', type=int, help='The file size limitation to filter files.')
            c.argument('file_last_written', type=int, help='Integer in hours to indicate file last modify time, default value is 72.')
            c.argument('filename_contains', help='The pattern that file name should match.')

    for scope in ['mariadb db', 'mysql db', 'postgres db']:
        with self.argument_context(scope) as c:
            c.argument('database_name', options_list=['--name', '-n'])

    for scope in ['mariadb server firewall-rule', 'mysql server firewall-rule', 'postgres server firewall-rule']:
        with self.argument_context(scope) as c:
            c.argument('server_name', options_list=['--server-name', '-s'])
            c.argument('firewall_rule_name', options_list=['--name', '-n'], id_part='child_name_1', help='The name of the firewall rule. The firewall rule name cannot be empty. The firewall rule name can only contain 0-9, a-z, A-Z, \'-\' and \'_\'. Additionally, the firewall rule name cannot exceed 128 characters.')
            c.argument('start_ip_address', options_list=['--start-ip-address'], help='The start IP address of the firewall rule. Must be IPv4 format. Use value \'0.0.0.0\' to represent all Azure-internal IP addresses.')
            c.argument('end_ip_address', options_list=['--end-ip-address'], help='The end IP address of the firewall rule. Must be IPv4 format. Use value \'0.0.0.0\' to represent all Azure-internal IP addresses.')

    for scope in ['mariadb server vnet-rule', 'mysql server vnet-rule', 'postgres server vnet-rule']:
        with self.argument_context(scope) as c:
            c.argument('server_name', options_list=['--server-name', '-s'])
            c.argument('virtual_network_rule_name', options_list=['--name', '-n'], id_part='child_name_1', help='The name of the vnet rule.')
            c.argument('virtual_network_subnet_id', options_list=['--subnet'], help='Name or ID of the subnet that allows access to an Azure Postgres Server. If subnet name is provided, --vnet-name must be provided.')
            c.argument('ignore_missing_vnet_service_endpoint', options_list=['--ignore-missing-endpoint', '-i'], help='Create vnet rule before virtual network has vnet service endpoint enabled', arg_type=get_three_state_flag())

    for scope in ['mariadb server vnet-rule create', 'mariadb server vnet-rule update', 'postgres server vnet-rule create', 'postgres server vnet-rule update', 'mysql server vnet-rule create', 'mysql server vnet-rule update']:
        with self.argument_context(scope) as c:
            c.extra('vnet_name', options_list=['--vnet-name'], help='The virtual network name', validator=validate_subnet)

    for scope in ['mariadb server configuration', 'mysql server configuration', 'postgres server configuration']:
        with self.argument_context(scope) as c:
            c.argument('server_name', options_list=['--server-name', '-s'])
            c.argument('configuration_name', id_part='child_name_1', options_list=['--name', '-n'])

    for scope in ['mariadb server replica list', 'mysql server replica list', 'postgres server replica list']:
        with self.argument_context(scope) as c:
            c.argument('server_name', options_list=['--server-name', '-s'], help='Name of the master server.')

    for item in ['approve', 'reject', 'delete', 'show']:
        for scope in ['mariadb server private-endpoint-connection {}', 'mysql server private-endpoint-connection {}', 'postgres server private-endpoint-connection {}']:
            with self.argument_context(scope.format(item)) as c:
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

    for scope in ['mariadb server private-link-resource', 'mysql server private-link-resource', 'postgres server private-link-resource']:
        with self.argument_context(scope) as c:
            c.argument('server_name', options_list=['--server-name', '-s'], required=True, help='Name of the Server.')

    for scope in ['mysql server key', 'postgres server key']:
        with self.argument_context(scope) as c:
            c.argument('server_name', options_list=['--name', '-s'])
            c.argument('kid', options_list=['--kid', '-k'], help='The Azure Key Vault key identifier of the server key. An example key identifier is "https://YourVaultName.vault.azure.net/keys/YourKeyName/01234567890123456789012345678901"')

    for scope in ['mysql server ad-admin', 'postgres server ad-admin']:
        with self.argument_context(scope) as c:
            c.argument('server_name', options_list=['--server-name', '-s'])
            c.argument('login', options_list=['--display-name', '-u'], help='Display name of the Azure AD administrator user or group.')
            c.argument('sid', options_list=['--object-id', '-i'], help='The unique ID of the Azure AD administrator.')


    # Flexible-server
    def _flexible_server_params(command_group):
        server_name_setter_arg_type = CLIArgumentType(configured_default='web', options_list=['--name', '-n'], metavar='NAME', help="Name of the server. The name can contain only lowercase letters, numbers, and the hyphen (-) character. Minimum 3 characters and maximum 63 characters.",
                                        local_context_attribute=LocalContextAttribute(name='server_name', 
                                        actions=[LocalContextAction.SET], scopes=['{} flexible-server'.format(command_group)]))

        server_name_arg_type = CLIArgumentType(configured_default='web', options_list=['--name', '-n'], metavar='NAME', help="Name of the server. The name can contain only lowercase letters, numbers, and the hyphen (-) character. Minimum 3 characters and maximum 63 characters.",
                                        local_context_attribute=LocalContextAttribute(name='server_name', 
                                        actions=[LocalContextAction.SET, LocalContextAction.GET], scopes=['{} flexible-server'.format(command_group)]))

        with self.argument_context('{} flexible-server create'.format(command_group)) as c:
            # c.extra('generate_password', help='Generate a password.', arg_group='Authentication')

            # Add create mode as a parameter
            if command_group == 'postgres':
                default_string = 'azurepg_'
                c.argument('tier', default='GeneralPurpose', help='Compute tier of the server. Accepted values: Burstable, GeneralPurpose, Memory Optimized ')
                c.argument('sku_name', default='Standard_D4s_v3', options_list=['--sku-name'], help='The name of the compute SKU. Follows the convention Standard_{VM name}. Examples: Standard_B1ms, Standard_D4s_v3 ')
                c.argument('storage_mb', default='131072', options_list=['--storage-size'], type=int, help='The storage capacity of the server. Minimum is 32 GiB and max is 16 TiB.')
                c.argument('version', default='12', help='Server major version.')              
            elif command_group == 'mysql':
                default_string = 'azuremysql_'
                c.argument('tier', default='Burstable', help='Compute tier of the server. Accepted values: Burstable, GeneralPurpose, Memory Optimized ')
                c.argument('sku_name', default='Standard_B1MS', options_list=['--sku-name'], help='The name of the compute SKU. Follows the convention Standard_{VM name}. Examples: Standard_B1ms, Standard_D4s_v3 ')
                c.argument('storage_mb', default='10240', options_list=['--storage-size'], type=int, help='The storage capacity of the server. Minimum is 5 GiB and increases in 1 GiB increments. Max is 16 TiB.')
                c.argument('version', default='5.7', help='Server major version.')
      
            c.argument('server_name', default=create_random_resource_name(default_string), arg_type=server_name_setter_arg_type)
            c.argument('resource_group_name', default=create_random_resource_name(default_string),  arg_type=resource_group_name_type)
            c.argument('location', arg_type=get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
            c.argument('administrator_login', default=generate_username(), options_list=['--admin-user, -u'],  arg_group='Authentication')
            c.argument('administrator_login_password', options_list=['--admin-password, -p'], arg_group='Authentication')

            c.argument('backup_retention', default='7', type=int, options_list=['--backup-retention'], help='The number of days a backup is retained. Range of 7 to 35 days. Default is 7 days.', validator=retention_validator)
            c.argument('tags', tags_type)
            c.argument('public_access', options_list=['--public-access'], help='Determines the public access. Enter single or range of IP addresses to be included in the allowed list of IPs. IP address ranges must be dash-separated and not contain any spaces. Specifying 0.0.0.0 allows public access from any resources deployed within Azure to access your server. Specifying no IP address sets the server in public access mode but does not create a firewall rule. ')
            # c.argument('vnet_name', option_list=['--vnet'])
            # c.argument('vnet_address_prefix', default='10.0.0.0/16', option_list=['--vnet-address-prefix'])
            # c.argument('subnet_name', option_list=['--subnet'])
            # c.argument('subnet_address_preefix', default='10.0.0.0/24', option_list=['--subnet-address-prefix'])
            c.argument('high_availability', options_list=['--high-availability'], help='')     
            c.ignore('database_name')
        
        with self.argument_context('{} flexible-server restore'.format(command_group)) as c:
            c.argument('source_server', options_list=['--source-server'], help='The name or resource ID of the source server to restore from.')
            c.argument('restore_point_in_time', help='The point in time to restore from (ISO8601 format), e.g., 2017-04-26T02:10:00+08:00')
        
        with self.argument_context('{} flexible-server update'.format(command_group)) as c:
            c.ignore('family', 'capacity', 'tier')
            c.argument('sku_name', options_list=['--sku-name'], help='The name of the sku. Follows the convention {pricing tier}_{compute generation}_{vCores} in shorthand. Examples: B_Gen5_1, GP_Gen5_4, MO_Gen5_16.')
            c.argument('assign_identity', options_list=['--assign-identity'], help='Generate and assign an Azure Active Directory Identity for this server for use with key management services like Azure KeyVault.')
            c.argument('storage_mb', options_list=['--storage-mb'], help ='The storage capacity of the server (unit is megabytes). Minimum 5120 and increases in 1024 increments. Default is 51200.') #storage size? storage mb?
            c.argument('tags', options_list=['--tags'], help='Space-separated tags: key[=value] [key[=value] ...]. Use \"\" to clear existing tags.')
            c.argument('backup_retention', options_list=['--backup-retention'], help='The number of days a backup is retained. Range of 7 to 35 days. Default is 7 days.', validator=retention_validator)

        for scope in ['delete', 'list', 'wait', 'show', 'restart', 'restore', 'update']:
            argument_context_string = '{} flexible-server {}'.format(command_group, scope)
            with self.argument_context(argument_context_string) as c:
                c.argument('resource_group_name', arg_type=resource_group_name_type)
                c.argument('server_name', arg_type=server_name_arg_type)

    _flexible_server_params('postgres')
    _flexible_server_params('mysql')
