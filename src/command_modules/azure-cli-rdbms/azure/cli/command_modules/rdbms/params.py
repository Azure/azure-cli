# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.mgmt.rdbms import mysql
from azure.mgmt.rdbms import postgresql

from azure.cli.core.commands import register_cli_argument
from azure.cli.core.commands.parameters import \
    (get_resource_name_completion_list, tags_type, enum_choice_list, location_type)
from ._util import PolyParametersContext
from .validators import configuration_value_validator

# pylint: disable=line-too-long

#        load parameters from models        #


def load_params(command_group, engine):
    with PolyParametersContext(command='{} server create'.format(command_group)) as c:
        c.expand('sku', engine.models.Sku)
        c.ignore('name')
        c.ignore('family')
        c.ignore('size')

        c.expand('properties', engine.models.ServerPropertiesForDefaultCreate)
        c.argument('administrator_login', arg_group='Authentication')
        c.argument('administrator_login_password', arg_group='Authentication')

        c.expand('parameters', engine.models.ServerForCreate)

        c.argument('location', location_type, required=False)

    with PolyParametersContext(command='{} server restore'.format(command_group)) as c:
        c.expand('sku', engine.models.Sku)
        c.ignore('name')
        c.ignore('family')
        c.ignore('size')
        c.ignore('tier')
        c.ignore('capacity')

        c.expand('properties', engine.models.ServerPropertiesForRestore)
        c.ignore('version')
        c.ignore('ssl_enforcement')
        c.ignore('storage_mb')

        c.expand('parameters', engine.models.ServerForCreate)
        c.ignore('tags')
        c.ignore('location')

        c.argument('source_server_id', options_list=('--source-server', '-s'),
                   help='The name or ID of the source server to restore from.')
        c.argument('restore_point_in_time',
                   help='The point in time to restore from (ISO8601 format), e.g., 2017-04-26T02:10:00+08:00')

    with PolyParametersContext(command='{} server configuration set'.format(command_group)) as c:
        c.ignore('source')
        c.argument('value',
                   help='Value of the configuration. If not provided, configuration value will be set to default.',
                   validator=configuration_value_validator)


load_params('mysql', mysql)
load_params('postgres', postgresql)

#####
#           register cli arguments
#####

server_completers = {'mysql': get_resource_name_completion_list('Microsoft.DBForMySQL/servers'),
                     'postgres': get_resource_name_completion_list('Microsoft.DBForPostgreSQL/servers')}


for command_group_name in ['mysql', 'postgres']:
    register_cli_argument('{0}'.format(command_group_name), 'name', options_list=('--sku-name',))
    register_cli_argument('{0}'.format(command_group_name), 'server_name', completer=server_completers[command_group_name], options_list=('--server-name', '-s'))

    register_cli_argument('{0} server'.format(command_group_name), 'server_name', options_list=('--name', '-n'), id_part='name',
                          help='Name of the server.')
    register_cli_argument('{0} server'.format(command_group_name), 'administrator_login', options_list=('--admin-user', '-u'))
    register_cli_argument('{0} server'.format(command_group_name), 'administrator_login_password', options_list=('--admin-password', '-p'), required=False,
                          help='The password of the administrator login.')
    register_cli_argument('{0} server'.format(command_group_name), 'ssl_enforcement', options_list=('--ssl-enforcement',),
                          help='Enable ssl enforcement or not when connect to server.',
                          **enum_choice_list(['Enabled', 'Disabled']))
    register_cli_argument('{0} server'.format(command_group_name), 'tier', options_list=('--performance-tier',),
                          help='The performance tier of the server.',
                          **enum_choice_list(['Basic', 'Standard']))
    register_cli_argument('{0} server'.format(command_group_name), 'capacity', options_list=('--compute-units',), type=int,
                          help='Number of compute units.')
    register_cli_argument('{0} server'.format(command_group_name), 'storage_mb', options_list=('--storage-size',), type=int,
                          help='The max storage size of the server, unit is MB.')
    register_cli_argument('{0} server'.format(command_group_name), 'tags', tags_type)

    register_cli_argument('{0} server-logs'.format(command_group_name), 'file_name', options_list=('--name', '-n'), nargs='+')
    register_cli_argument('{0} server-logs'.format(command_group_name), 'max_file_size', type=int)
    register_cli_argument('{0} server-logs'.format(command_group_name), 'file_last_written', type=int)

    register_cli_argument('{0} db'.format(command_group_name), 'database_name', options_list=('--name', '-n'))

    register_cli_argument('{0} server firewall-rule'.format(command_group_name), 'server_name', options_list=('--server-name', '-s'))
    register_cli_argument('{0} server firewall-rule'.format(command_group_name), 'firewall_rule_name', options_list=('--name', '-n'), id_part='child_name',
                          help='The name of the firewall rule.')
    register_cli_argument('{0} server firewall-rule'.format(command_group_name), 'start_ip_address', options_list=('--start-ip-address',),
                          help='The start IP address of the firewall rule. Must be IPv4 format.')
    register_cli_argument('{0} server firewall-rule'.format(command_group_name), 'end_ip_address', options_list=('--end-ip-address',),
                          help='The end IP address of the firewall rule. Must be IPv4 format.')

    register_cli_argument('{0} server configuration'.format(command_group_name), 'server_name', options_list=('--server-name', '-s'))
    register_cli_argument('{0} server configuration'.format(command_group_name), 'configuration_name', id_part='child_name', options_list=('--name', '-n'))
