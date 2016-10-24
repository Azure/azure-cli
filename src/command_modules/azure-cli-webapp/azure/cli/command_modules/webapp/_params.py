#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
from azure.cli.core.commands import register_cli_argument

from azure.mgmt.web import WebSiteManagementClient
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.parameters import (resource_group_name_type, location_type,
                                                get_resource_name_completion_list,
                                                CliArgumentType, ignore_type, enum_choice_list)

# FACTORIES
def web_client_factory(**_):
    return get_mgmt_service_client(WebSiteManagementClient)

def _generic_site_operation(resource_group_name, name, operation_name, slot=None, #pylint: disable=too-many-arguments
                            extra_parameter=None, client=None):
    client = client or web_client_factory()
    m = getattr(client.sites,
                operation_name if slot is None else operation_name + '_slot')
    if slot is None:
        return (m(resource_group_name, name)
                if extra_parameter is None else m(resource_group_name, name, extra_parameter))
    else:
        return (m(resource_group_name, name, slot)
                if extra_parameter is None else m(resource_group_name, name, extra_parameter, slot))

def get_hostname_completion_list(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
    if parsed_args.resource_group_name and parsed_args.webapp:
        rg = parsed_args.resource_group_name
        webapp = parsed_args.webapp
        slot = getattr(parsed_args, 'slot', None)
        result = _generic_site_operation(rg, webapp, 'get_site_host_name_bindings', slot)
        #workaround an api defect, that 'name' is '<webapp>/<hostname>'
        return [r.name.split('/', 1)[1] for r in result]

#pylint: disable=line-too-long
# PARAMETER REGISTRATION
name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')
sku_arg_type = CliArgumentType(help='The pricing tiers, e.g., F1(Free), D1(Shared), B1(Basic Small), B2(Basic Medium), B3(Basic Large), S1(Standard Small), P1(Premium Small), etc',
                               **enum_choice_list(['F1', 'FREE', 'D1', 'SHARED', 'B1', 'B2', 'B3', 'S1', 'S2', 'S3', 'P1', 'P2', 'P3']))

register_cli_argument('appservice', 'resource_group_name', arg_type=resource_group_name_type)
register_cli_argument('appservice', 'location', arg_type=location_type)

register_cli_argument('appservice list-locations', 'linux_workers_enabled', action='store_true', help='get regions which support hosting webapps on Linux workers')
register_cli_argument('appservice plan', 'name', arg_type=name_arg_type, help='The name of the app service plan', completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'), id_part='name')
register_cli_argument('appservice plan create', 'name', options_list=('--name', '-n'), help="Name of the new app service plan")
register_cli_argument('appservice plan create', 'sku', arg_type=sku_arg_type, default='B1')
register_cli_argument('appservice plan create', 'is_linux', action='store_true', required=False, help='host webapp on Linux worker')
register_cli_argument('appservice plan update', 'sku', arg_type=sku_arg_type)
register_cli_argument('appservice plan update', 'allow_pending_state', ignore_type)
register_cli_argument('appservice plan', 'number_of_workers', help='Number of workers to be allocated.', type=int, default=1)
register_cli_argument('appservice plan', 'admin_site_name', help='The name of the admin web app.')

register_cli_argument('appservice web', 'slot', help="the name of the slot. Default to the productions slot if not specified")
register_cli_argument('appservice web', 'name', arg_type=name_arg_type, completer=get_resource_name_completion_list('Microsoft.Web/sites'), id_part='name')
register_cli_argument('appservice web create', 'name', options_list=('--name', '-n'), help='name of the new webapp')
register_cli_argument('appservice web create', 'plan', options_list=('--plan',), completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                      help="name or resource id of the app service plan. Use 'appservice plan create' to get one")

register_cli_argument('appservice web deployment user', 'user_name', help='user name')
register_cli_argument('appservice web deployment user', 'password', help='password, will prompt if not specified')

register_cli_argument('appservice web deployment slot', 'slot', help='the name of the slot')
register_cli_argument('appservice web deployment slot', 'webapp', help='Name of the webapp')
register_cli_argument('appservice web deployment slot', 'auto_swap_slot', help='target slot to swap', default='production')
register_cli_argument('appservice web deployment slot', 'disable', help='disable auto swap', action='store_true')

two_states_switch = ['true', 'false']

register_cli_argument('appservice web log config', 'application_logging', help='configure application logging to file system', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web log config', 'detailed_error_messages', help='configure detailed error messages', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web log config', 'failed_request_tracing', help='configure failed request tracing', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web log config', 'level', help='logging level', **enum_choice_list(['error', 'warning', 'information', 'verbose']))
server_log_switch_options = ['off', 'storage', 'filesystem']
register_cli_argument('appservice web log config', 'web_server_logging', help='configure Web server logging', **enum_choice_list(server_log_switch_options))

register_cli_argument('appservice web log tail', 'provider', help="scope the live traces to certain providers/folders, for example:'application', 'http' for server log, 'kudu/trace', etc")
register_cli_argument('appservice web log download', 'log_file', default='webapp_logs.zip', help='the downloaded zipped log file path')

register_cli_argument('appservice web config appsettings', 'settings', nargs='+', help="space separated app settings in a format of <name>=<value>")
register_cli_argument('appservice web config appsettings', 'setting_names', nargs='+', help="space separated app setting names")

register_cli_argument('appservice web config container', 'docker_registry_server_url', help='the container registry server url')
register_cli_argument('appservice web config container', 'docker_custom_image_name', help='the container custom image name and optionally the tag name')
register_cli_argument('appservice web config container', 'docker_registery_server_user', help='the container registry server username')
register_cli_argument('appservice web config container', 'docker_registery_server_password', help='the container registry server password')

register_cli_argument('appservice web config update', 'remote_debugging_enabled', help='enable or disable remote debugging', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web config update', 'web_sockets_enabled', help='enable or disable web sockets', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web config update', 'always_on', help='ensure webapp gets loaded all the time, rather unloaded after been idle. Recommended when you have continuous web jobs running', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web config update', 'auto_heal_enabled', help='enable or disable auto heal', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web config update', 'use32_bit_worker_process', options_list=('--use-32bit-worker-process',), help='use 32 bits worker process or not', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web config update', 'php_version', help='The version used to run your web app if using PHP, e.g., 5.5, 5.6, 7.0')
register_cli_argument('appservice web config update', 'python_version', help='The version used to run your web app if using Python, e.g., 2.7, 3.4')
register_cli_argument('appservice web config update', 'net_framework_version', help="The version used to run your web app if using .NET Framework, e.g., 'v4.0' for .NET 4.6 and 'v3.0' for .NET 3.5")
register_cli_argument('appservice web config update', 'java_version', help="The version used to run your web app if using Java, e.g., '1.7' for Java 7, '1.8' for Java 8")
register_cli_argument('appservice web config update', 'java_container', help="The java container, e.g., Tomcat, Jetty")
register_cli_argument('appservice web config update', 'java_container_version', help="The version of the java container, e.g., '8.0.23' for Tomcat")
register_cli_argument('appservice web config update', 'app_command_line', options_list=('--startup-file',), help="The startup file for linux hosted web apps, e.g. 'process.json' for Node.js web")

register_cli_argument('appservice web config hostname', 'webapp', help="webapp name", completer=get_resource_name_completion_list('Microsoft.Web/sites'), id_part='name')
register_cli_argument('appservice web config hostname', 'name', arg_type=name_arg_type, completer=get_hostname_completion_list, help="hostname assigned to the site, such as custom domains", id_part='child_name')
