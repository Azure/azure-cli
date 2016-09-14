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

register_cli_argument('webapp', 'resource_group', arg_type=resource_group_name_type)
register_cli_argument('webapp', 'location', arg_type=location_type)
register_cli_argument('webapp', 'slot', help="the name of the slot. Default to the productions slot if not specified")
register_cli_argument('webapp plan', 'name', arg_type=existing_plan_name)
register_cli_argument('webapp plan create', 'name', options_list=('--name', '-n'), help="Name of the new app service plan")

#TODO: be in parity with xplat, merge 'worker_size' option into 'tier'
register_cli_argument('webapp plan', 'tier', choices=['Free', 'Shared', 'Basic', 'Standard', 'Premium'], default='Free', help='The app service plan tier')
register_cli_argument('webapp plan', 'worker_size', choices=['Small', 'Medium', 'Large', 'ExtraLarge'], default='Small', help='Size of workers to be allocated')

register_cli_argument('webapp plan', 'number_of_workers', help='Number of workers to be allocated.', type=int, default=1)
register_cli_argument('webapp plan', 'admin_site_name', help='The name of the admin web app.')

register_cli_argument('webapp', 'name', arg_type=existing_webapp_name)
register_cli_argument('webapp create', 'name', options_list=('--name', '-n'), help='name of the new webapp')
register_cli_argument('webapp create', 'plan', help="name or resource id of the app service plan. Use 'webapp plan create' to get one")

register_cli_argument('webapp deployment user', 'user_name', help='user name')
register_cli_argument('webapp deployment user', 'password', help='password, will prompt if not specified')

register_cli_argument('webapp deployment slot', 'slot', help='the name of the slot')
register_cli_argument('webapp deployment slot', 'webapp', help='Name of the webapp')
register_cli_argument('webapp deployment slot', 'auto_swap_slot', help='target slot to swap', default='production')
register_cli_argument('webapp deployment slot', 'disable', help='disable auto swap', action='store_true')

switch_options = ['on', 'off']
register_cli_argument('webapp log set', 'application_logging', choices=switch_options, type=str.lower, help='configure application logging to file system')
server_log_switch_options = ['off', 'storage', 'filesystem']
register_cli_argument('webapp log set', 'web_server_logging', choices=server_log_switch_options, type=str.lower, help='configure Web server logging')
register_cli_argument('webapp log set', 'detailed_error_messages', choices=switch_options, type=str.lower, help='configure detailed error messages')
register_cli_argument('webapp log set', 'failed_request_tracing', choices=switch_options, type=str.lower, help='configure failed request tracing')
register_cli_argument('webapp log set', 'level', choices=['error', 'warning', 'information', 'verbose'], type=str.lower, help='logging level')

register_cli_argument('webapp log tail', 'provider', help="scope the live traces to certain providers/folders, for example:'application', 'http' for server log, 'kudu/trace', etc")
register_cli_argument('webapp log download', 'log_file', default='webapp_logs.zip', help='the downloaded zipped log file path')

register_cli_argument('webapp config appsettings', 'settings', nargs='+', help="space separated app settings in a format of 'name'='value'")
register_cli_argument('webapp config appsettings', 'setting_names', nargs='+', help="space separated app setting names")
