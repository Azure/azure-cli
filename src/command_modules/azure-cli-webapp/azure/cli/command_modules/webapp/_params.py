#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
from azure.cli.core.commands import register_cli_argument

from azure.mgmt.web import WebSiteManagementClient
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.parameters import (resource_group_name_type, location_type,
                                                CliArgumentType)

# FACTORIES
def web_client_factory(**_):
    return get_mgmt_service_client(WebSiteManagementClient)

def list_webapp_names(prefix, action, parsed_args, **kwargs):#pylint: disable=unused-argument
    if parsed_args.resource_group_name:
        client = web_client_factory()
        #pylint: disable=no-member
        result = client.sites.get_sites(parsed_args.resource_group_name).value
        return [x.name for x in result]

def list_app_service_plan_names(prefix, action, parsed_args, **kwargs):#pylint: disable=unused-argument
    if parsed_args.resource_group_name:
        client = web_client_factory()
        #pylint: disable=no-member
        result = client.server_farms.get_server_farms(parsed_args.resource_group_name).value
        return [x.name for x in result]

#pylint: disable=line-too-long
# PARAMETER REGISTRATION
name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')
existing_plan_name = CliArgumentType(overrides=name_arg_type, help='The name of the app service plan', completer=list_app_service_plan_names, id_part='name')
existing_webapp_name = CliArgumentType(overrides=name_arg_type, help='The name of the web app', completer=list_webapp_names, id_part='name')

register_cli_argument('appservice web', 'resource_group', arg_type=resource_group_name_type)
register_cli_argument('appservice web', 'location', arg_type=location_type)
register_cli_argument('appservice web', 'slot', help="the name of the slot. Default to the productions slot if not specified")

register_cli_argument('appservice plan', 'resource_group', arg_type=resource_group_name_type)
register_cli_argument('appservice plan', 'location', arg_type=location_type)
register_cli_argument('appservice plan', 'name', arg_type=existing_plan_name)
register_cli_argument('appservice plan create', 'name', options_list=('--name', '-n'), help="Name of the new app service plan")
register_cli_argument('appservice plan', 'tier', type=str.upper, choices=['FREE', 'SHARED', 'B1', 'B2', 'B3', 'S1', 'S2', 'S3', 'P1', 'P2', 'P3'], default='B1',
                      help='The pricing tiers, e.g., FREE, SHARED, B1(Basic Small), B2(Basic Medium), B3(Basic Large), S1(Standard Small), P1(Premium Small), etc')
register_cli_argument('appservice plan', 'number_of_workers', help='Number of workers to be allocated.', type=int, default=1)
register_cli_argument('appservice plan', 'admin_site_name', help='The name of the admin web app.')

register_cli_argument('appservice web', 'name', arg_type=existing_webapp_name)
register_cli_argument('appservice web create', 'name', options_list=('--name', '-n'), help='name of the new webapp')
register_cli_argument('appservice web create', 'plan', help="name or resource id of the app service plan. Use 'appservice plan create' to get one")

register_cli_argument('appservice web deployment user', 'user_name', help='user name')
register_cli_argument('appservice web deployment user', 'password', help='password, will prompt if not specified')

register_cli_argument('appservice web deployment slot', 'slot', help='the name of the slot')
register_cli_argument('appservice web deployment slot', 'webapp', help='Name of the webapp')
register_cli_argument('appservice web deployment slot', 'auto_swap_slot', help='target slot to swap', default='production')
register_cli_argument('appservice web deployment slot', 'disable', help='disable auto swap', action='store_true')

two_states_switch = [True, False]
def two_states_switch_type(value=None):
    if value is None:
        return None
    if value.lower() in ['true', 'false']:
        return value.lower() == 'true'
    return value

register_cli_argument('appservice web log set', 'application_logging', choices=two_states_switch, type=two_states_switch_type, help='configure application logging to file system')
register_cli_argument('appservice web log set', 'detailed_error_messages', choices=two_states_switch, type=two_states_switch_type, help='configure detailed error messages')
register_cli_argument('appservice web log set', 'failed_request_tracing', choices=two_states_switch, type=two_states_switch_type, help='configure failed request tracing')
register_cli_argument('appservice web log set', 'level', choices=['error', 'warning', 'information', 'verbose'], type=str.lower, help='logging level')
server_log_switch_options = ['off', 'storage', 'filesystem']
register_cli_argument('appservice web log set', 'web_server_logging', choices=server_log_switch_options, type=str.lower, help='configure Web server logging')

register_cli_argument('appservice web log tail', 'provider', help="scope the live traces to certain providers/folders, for example:'application', 'http' for server log, 'kudu/trace', etc")
register_cli_argument('appservice web log download', 'log_file', default='webapp_logs.zip', help='the downloaded zipped log file path')

register_cli_argument('appservice web config appsettings', 'settings', nargs='+', help="space separated app settings in a format of <name>=<value>")
register_cli_argument('appservice web config appsettings', 'setting_names', nargs='+', help="space separated app setting names")

register_cli_argument('appservice web config update', 'remote_debugging_enabled', choices=two_states_switch, type=two_states_switch_type, help='enable or disable remote debugging')
register_cli_argument('appservice web config update', 'web_sockets_enabled', choices=two_states_switch, type=two_states_switch_type, help='enable or disable web sockets')
register_cli_argument('appservice web config update', 'always_on', choices=two_states_switch, type=two_states_switch_type, help='ensure webapp gets loaded all the time, rather unloaded after been idle. Recommended when you have continuous web jobs running')
register_cli_argument('appservice web config update', 'auto_heal_enabled', choices=two_states_switch, type=two_states_switch_type, help='enable or disable auto heal')
register_cli_argument('appservice web config update', 'use32_bit_worker_process', options_list=('--use-32bit-worker-process',), choices=two_states_switch, type=two_states_switch_type, help='use 32 bits worker process or not')

register_cli_argument('appservice web config update', 'php_version', help='The version used to run your web app if using PHP, e.g., 5.5, 5.6, 7.0')
register_cli_argument('appservice web config update', 'python_version', help='The version used to run your web app if using Python, e.g., 2.7, 3.4')
register_cli_argument('appservice web config update', 'net_framework_version', help="The version used to run your web app if using .NET Framework, e.g., 'v4.0' for .NET 4.6 and 'v3.0' for .NET 3.5")
register_cli_argument('appservice web config update', 'java_version', help="The version used to run your web app if using Java, e.g., '1.7' for Java 7, '1.8' for Java 8")
register_cli_argument('appservice web config update', 'java_container', help="The java container, e.g., Tomcat, Jetty")
register_cli_argument('appservice web config update', 'java_container_version', help="The version of the java container, e.g., '8.0.23' for Tomcat")
