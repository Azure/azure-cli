# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands.parameters import get_resource_name_completion_list, tags_type, get_location_type, get_enum_type   # pylint: disable=line-too-long
from azure.mgmt.rdbms import mysql, postgresql
from azure.cli.command_modules.rdbms.validators import configuration_value_validator


def load_arguments(self, _):    # pylint: disable=too-many-statements

    server_completers = {
        'mysql': get_resource_name_completion_list('Microsoft.DBForMySQL/servers'),
        'postgres': get_resource_name_completion_list('Microsoft.DBForPostgreSQL/servers')
    }

    def _complex_params(command_group, engine):
        with self.argument_context('{} server create'.format(command_group)) as c:
            c.expand('sku', engine.models.Sku)
            c.ignore('size', 'family', 'capacity', 'tier')
            c.expand('storage_profile', engine.models.storage_profile.StorageProfile)
            c.expand('properties', engine.models.ServerPropertiesForDefaultCreate)
            c.argument('administrator_login', required=True, arg_group='Authentication')
            c.argument('administrator_login_password', arg_group='Authentication')

            c.expand('parameters', engine.models.ServerForCreate)
            c.argument('location', arg_type=get_location_type(self.cli_ctx), required=False)

        with self.argument_context('{} server restore'. format(command_group)) as c:
            c.ignore('sku', 'storage_profile')

            c.expand('properties', engine.models.ServerPropertiesForRestore)
            c.ignore('version', 'ssl_enforcement', 'storage_mb')

            c.expand('parameters', engine.models.ServerForCreate)
            c.ignore('tags', 'location')

            c.argument('source_server_id', options_list=['--source-server', '-s'], help='The name or ID of the source server to restore from.')
            c.argument('restore_point_in_time', help='The point in time to restore from (ISO8601 format), e.g., 2017-04-26T02:10:00+08:00')

        with self.argument_context('{} server configuration set'.format(command_group)) as c:
            c.argument('value', help='Value of the configuration. If not provided, configuration value will be set to default.', validator=configuration_value_validator)
            c.ignore('source')

        with self.argument_context('{} server wait'.format(command_group)) as c:
            c.ignore('created', 'deleted', 'updated')

    _complex_params('mysql', mysql)
    _complex_params('postgres', postgresql)

    for scope in ['mysql', 'postgres']:
        with self.argument_context(scope) as c:
            c.argument('name', options_list=['--sku-name'], required=True)
            c.argument('server_name', completer=server_completers[scope], options_list=['--server-name', '-s'], help='Name of the server.')

    for scope in ['mysql server', 'postgres server']:
        with self.argument_context(scope) as c:
            c.ignore('size', 'family', 'capacity', 'tier')

            c.argument('server_name', options_list=['--name', '-n'], id_part='name', help='Name of the server.')
            c.argument('administrator_login', options_list=['--admin-user', '-u'])
            c.argument('administrator_login_password', options_list=['--admin-password', '-p'], help='The password of the administrator login.')
            c.argument('ssl_enforcement', arg_type=get_enum_type(['Enabled', 'Disabled']), options_list=['--ssl-enforcement'], help='Enable ssl enforcement or not when connect to server.')
            c.argument('tier', arg_type=get_enum_type(['Basic', 'GeneralPurpose', 'MemoryOptimized']), options_list=['--performance-tier'], help='The performance tier of the server.')
            c.argument('capacity', options_list=['--vcore'], type=int, help='Number of vcore.')
            c.argument('family', options_list=['--family'], arg_type=get_enum_type(['Gen4', 'Gen5']), help='Hardware generation.')
            c.argument('storage_mb', options_list=['--storage-size'], type=int, help='The max storage size of the server. Unit is megabytes.')
            c.argument('backup_retention_days', options_list=['--backup-retention'], type=int, help='The number of days a backup is retained.')
            c.argument('tags', tags_type)

    for scope in ['mysql server-logs', 'postgres server-logs']:
        with self.argument_context(scope) as c:
            c.argument('file_name', options_list=['--name', '-n'], nargs='+', help='Space-separated list of log filenames on the server to download.')
            c.argument('max_file_size', type=int, help='The file size limitation to filter files.')
            c.argument('file_last_written', type=int, help='Integer in hours to indicate file last modify time, default value is 72.')
            c.argument('filename_contains', help='The pattern that file name should match.')

    for scope in ['mysql db', 'postgres db']:
        with self.argument_context(scope) as c:
            c.argument('database_name', options_list=['--name', '-n'])

    for scope in ['mysql server firewall-rule', 'postgres server firewall-rule']:
        with self.argument_context(scope) as c:
            c.argument('server_name', options_list=['--server-name', '-s'])
            c.argument('firewall_rule_name', options_list=['--name', '-n'], id_part='child_name_1', help='The name of the firewall rule.')
            c.argument('start_ip_address', options_list=['--start-ip-address'], help='The start IP address of the firewall rule. Must be IPv4 format. Use value \'0.0.0.0\' to represent all Azure-internal IP addresses.')
            c.argument('end_ip_address', options_list=['--end-ip-address'], help='The end IP address of the firewall rule. Must be IPv4 format. Use value \'0.0.0.0\' to represent all Azure-internal IP addresses.')

    for scope in ['mysql server configuration', 'postgres server configuration']:
        with self.argument_context(scope) as c:
            c.argument('server_name', options_list=['--server-name', '-s'])
            c.argument('configuration_name', id_part='child_name_1', options_list=['--name', '-n'])
