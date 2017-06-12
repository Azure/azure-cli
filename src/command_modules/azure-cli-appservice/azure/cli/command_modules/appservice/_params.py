# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from argcomplete.completers import FilesCompleter

from azure.cli.core.commands import register_cli_argument
from azure.cli.core.commands.parameters import (resource_group_name_type, location_type,
                                                get_resource_name_completion_list, file_type,
                                                CliArgumentType, ignore_type, enum_choice_list)
from azure.mgmt.web.models import DatabaseType, ConnectionStringType
from ._client_factory import web_client_factory
from ._validators import validate_existing_function_app, validate_existing_web_app


def _generic_site_operation(resource_group_name, name, operation_name, slot=None,
                            extra_parameter=None, client=None):
    client = client or web_client_factory()
    m = getattr(client.web_apps,
                operation_name if slot is None else operation_name + '_slot')
    if slot is None:
        return (m(resource_group_name, name)
                if extra_parameter is None else m(resource_group_name, name, extra_parameter))

    return (m(resource_group_name, name, slot)
            if extra_parameter is None else m(resource_group_name, name, extra_parameter, slot))


def get_hostname_completion_list(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
    if parsed_args.resource_group_name and parsed_args.webapp:
        rg = parsed_args.resource_group_name
        webapp = parsed_args.webapp
        slot = getattr(parsed_args, 'slot', None)
        result = _generic_site_operation(rg, webapp, 'get_site_host_name_bindings', slot)
        # workaround an api defect, that 'name' is '<webapp>/<hostname>'
        return [r.name.split('/', 1)[1] for r in result]


# pylint: disable=line-too-long
# PARAMETER REGISTRATION
name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')
sku_arg_type = CliArgumentType(help='The pricing tiers, e.g., F1(Free), D1(Shared), B1(Basic Small), B2(Basic Medium), B3(Basic Large), S1(Standard Small), P1(Premium Small), etc',
                               **enum_choice_list(['F1', 'FREE', 'D1', 'SHARED', 'B1', 'B2', 'B3', 'S1', 'S2', 'S3', 'P1', 'P2', 'P3']))
webapp_name_arg_type = CliArgumentType(configured_default='web', options_list=('--name', '-n'), metavar='NAME',
                                       completer=get_resource_name_completion_list('Microsoft.Web/sites'), id_part='name',
                                       help="name of the web. You can configure the default using 'az configure --defaults web=<name>'")

# use this hidden arg to give a command the right instance, that functionapp commands
# work on function app and webapp ones work on web app
register_cli_argument('webapp', 'app_instance', ignore_type)
register_cli_argument('functionapp', 'app_instance', ignore_type)
# function app doesn't have slot support
register_cli_argument('functionapp', 'slot', ignore_type)

register_cli_argument('appservice', 'resource_group_name', arg_type=resource_group_name_type)
register_cli_argument('appservice', 'location', arg_type=location_type)

register_cli_argument('appservice list-locations', 'linux_workers_enabled', action='store_true', help='get regions which support hosting webapps on Linux workers')
register_cli_argument('appservice list-locations', 'sku', arg_type=sku_arg_type)
register_cli_argument('appservice plan', 'name', arg_type=name_arg_type, help='The name of the app service plan', completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'), id_part='name')
register_cli_argument('appservice plan create', 'name', options_list=('--name', '-n'), help="Name of the new app service plan", completer=None)
register_cli_argument('appservice plan create', 'sku', arg_type=sku_arg_type)
register_cli_argument('appservice plan create', 'is_linux', action='store_true', required=False, help='host webapp on Linux worker')
register_cli_argument('appservice plan update', 'sku', arg_type=sku_arg_type)
register_cli_argument('appservice plan update', 'allow_pending_state', ignore_type)
register_cli_argument('appservice plan', 'number_of_workers', help='Number of workers to be allocated.', type=int, default=1)
register_cli_argument('appservice plan', 'admin_site_name', help='The name of the admin web app.')

# new ones
register_cli_argument('webapp', 'resource_group_name', arg_type=resource_group_name_type)
register_cli_argument('webapp', 'location', arg_type=location_type)

register_cli_argument('webapp', 'slot', options_list=('--slot', '-s'), help="the name of the slot. Default to the productions slot if not specified")
register_cli_argument('webapp', 'name', configured_default='web',
                      arg_type=name_arg_type, completer=get_resource_name_completion_list('Microsoft.Web/sites'), id_part='name',
                      help="name of the web. You can configure the default using 'az configure --defaults web=<name>'")
register_cli_argument('webapp create', 'name', options_list=('--name', '-n'), help='name of the new webapp')
register_cli_argument('webapp create', 'deployment_container_image_name', options_list=('--deployment-container-image-name', '-i'),
                      help='Linux only. Container image name from Docker Hub, e.g. publisher/image-name:version')
register_cli_argument('webapp create', 'startup_file', help="Linux only. The web's startup file")
register_cli_argument('webapp create', 'runtime', options_list=('--runtime', '-r'), help="canonicalized web runtime in the format of Framework|Version, e.g. PHP|5.6. Use 'az webapp list-runtimes' for available list")  # TODO ADD completer
register_cli_argument('webapp list-runtimes', 'linux', action='store_true', help='list runtime stacks for linux based webapps')  # TODO ADD completer
register_cli_argument('webapp traffic-routing', 'distribution', options_list=('--distribution', '-d'), nargs='+', help='space separated slot routings in a format of <slot-name>=<percentage> e.g. staging=50. Unused traffic percentage will go to the Production slot')

register_cli_argument('webapp create', 'plan', options_list=('--plan', '-p'), completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                      help="name or resource id of the app service plan. Use 'appservice plan create' to get one")

register_cli_argument('webapp browse', 'logs', options_list=('--logs', '-l'), action='store_true', help='Enable viewing the log stream immediately after launching the web app')

for scope in ['webapp', 'functionapp']:
    register_cli_argument(scope + ' config ssl bind', 'ssl_type', help='The ssl cert type', **enum_choice_list(['SNI', 'IP']))
    register_cli_argument(scope + ' config ssl upload', 'certificate_password', help='The ssl cert password')
    register_cli_argument(scope + ' config ssl upload', 'certificate_file', type=file_type, help='The filepath for the .pfx file')
    register_cli_argument(scope + ' config ssl', 'certificate_thumbprint', help='The ssl cert thumbprint')
    register_cli_argument(scope + ' config appsettings', 'settings', nargs='+', help="space separated app settings in a format of <name>=<value>")
    register_cli_argument(scope + ' config appsettings', 'setting_names', nargs='+', help="space separated app setting names")
    register_cli_argument(scope + ' config hostname', 'hostname', completer=get_hostname_completion_list, help="hostname assigned to the site, such as custom domains", id_part='child_name')
    register_cli_argument(scope + ' deployment user', 'user_name', help='user name')
    register_cli_argument(scope + ' deployment user', 'password', help='password, will prompt if not specified')
    register_cli_argument(scope + ' deployment source', 'manual_integration', action='store_true', help='disable automatic sync between source control and web')
    register_cli_argument(scope + ' deployment source', 'repo_url', options_list=('--repo-url', '-u'), help='repository url to pull the latest source from, e.g. https://github.com/foo/foo-web')
    register_cli_argument(scope + ' deployment source', 'branch', help='the branch name of the repository')
    register_cli_argument(scope + ' deployment source', 'cd_provider', help='type of CI/CD provider', default='kudu', **enum_choice_list(['kudu', 'vsts']))
    register_cli_argument(scope + ' deployment source', 'cd_app_type', arg_group='VSTS CD Provider', help='web application framework you used to develop your app', default='AspNetWap', **enum_choice_list(['AspNetWap', 'AspNetCore', 'NodeJSWithGulp', 'NodeJSWithGrunt']))
    register_cli_argument(scope + ' deployment source', 'cd_account', arg_group='VSTS CD Provider', help='name of the Team Services account to create/use for continuous delivery')
    register_cli_argument(scope + ' deployment source', 'cd_account_must_exist', arg_group='VSTS CD Provider', help='specifies that the account must already exist. If not specified, the account will be created if it does not already exist (existing accounts are updated)', action='store_true')
    register_cli_argument(scope + ' deployment source', 'repository_type', help='repository type', default='git', **enum_choice_list(['git', 'mercurial']))
    register_cli_argument(scope + ' deployment source', 'git_token', help='git access token required for auto sync')
    register_cli_argument(scope + ' create', 'deployment_local_git', action='store_true', options_list=('--deployment-local-git', '-l'), help='enable local git')
    register_cli_argument(scope + ' create', 'deployment_source_url', options_list=('--deployment-source-url', '-u'), help='Git repository URL to link with manual integration')
    register_cli_argument(scope + ' create', 'deployment_source_branch', options_list=('--deployment-source-branch', '-b'), help='the branch to deploy')

register_cli_argument('webapp config hostname', 'webapp_name', help="webapp name. You can configure the default using 'az configure --defaults web=<name>'", configured_default='web',
                      completer=get_resource_name_completion_list('Microsoft.Web/sites'), id_part='name')
register_cli_argument('webapp config appsettings', 'slot_settings', nargs='+', help="space separated slot app settings in a format of <name>=<value>")

register_cli_argument('webapp deployment slot', 'slot', help='the name of the slot')
register_cli_argument('webapp deployment slot', 'webapp', arg_type=name_arg_type, completer=get_resource_name_completion_list('Microsoft.Web/sites'),
                      help='Name of the webapp', id_part='name')
register_cli_argument('webapp deployment slot', 'auto_swap_slot', help='target slot to auto swap', default='production')
register_cli_argument('webapp deployment slot', 'disable', help='disable auto swap', action='store_true')
register_cli_argument('webapp deployment slot', 'target_slot', help="target slot to swap, default to 'production'")
register_cli_argument('webapp deployment slot create', 'configuration_source', help="source slot to clone configurations from. Use webapp's name to refer to the production slot")
register_cli_argument('webapp deployment slot swap', 'action', help="swap types. use 'preview' to apply target slot's settings on the source slot first; use 'swap' to complete it; use 'reset' to reset the swap",
                      **enum_choice_list(['swap', 'preview', 'reset']))


two_states_switch = ['true', 'false']

register_cli_argument('webapp log config', 'application_logging', help='configure application logging to file system', **enum_choice_list(two_states_switch))
register_cli_argument('webapp log config', 'detailed_error_messages', help='configure detailed error messages', **enum_choice_list(two_states_switch))
register_cli_argument('webapp log config', 'failed_request_tracing', help='configure failed request tracing', **enum_choice_list(two_states_switch))
register_cli_argument('webapp log config', 'level', help='logging level', **enum_choice_list(['error', 'warning', 'information', 'verbose']))
server_log_switch_options = ['off', 'storage', 'filesystem']
register_cli_argument('webapp log config', 'web_server_logging', help='configure Web server logging', **enum_choice_list(server_log_switch_options))

register_cli_argument('webapp log tail', 'provider', help="By default all live traces configured by 'az webapp log config' will be shown, but you can scope to certain providers/folders, e.g. 'application', 'http', etc. For details, check out https://github.com/projectkudu/kudu/wiki/Diagnostic-Log-Stream")
register_cli_argument('webapp log download', 'log_file', default='webapp_logs.zip', type=file_type, completer=FilesCompleter(), help='the downloaded zipped log file path')

for scope in ['appsettings', 'connection-string']:
    register_cli_argument('webapp config ' + scope, 'settings', nargs='+', help="space separated {} in a format of <name>=<value>".format(scope))
    register_cli_argument('webapp config ' + scope, 'slot_settings', nargs='+', help="space separated slot {} in a format of <name>=<value>".format(scope))
    register_cli_argument('webapp config ' + scope, 'setting_names', nargs='+', help="space separated {} names".format(scope))
register_cli_argument('webapp config connection-string', 'connection_string_type',
                      options_list=('--connection-string-type', '-t'), help='connection string type', **enum_choice_list(ConnectionStringType))

register_cli_argument('webapp config container', 'docker_registry_server_url', options_list=('--docker-registry-server-url', '-r'), help='the container registry server url')
register_cli_argument('webapp config container', 'docker_custom_image_name', options_list=('--docker-custom-image-name', '-c'), help='the container custom image name and optionally the tag name')
register_cli_argument('webapp config container', 'docker_registry_server_user', options_list=('--docker-registry-server-user', '-u'), help='the container registry server username')
register_cli_argument('webapp config container', 'docker_registry_server_password', options_list=('--docker-registry-server-password', '-p'), help='the container registry server password')

register_cli_argument('webapp config set', 'remote_debugging_enabled', help='enable or disable remote debugging', **enum_choice_list(two_states_switch))
register_cli_argument('webapp config set', 'web_sockets_enabled', help='enable or disable web sockets', **enum_choice_list(two_states_switch))
register_cli_argument('webapp config set', 'always_on', help='ensure webapp gets loaded all the time, rather unloaded after been idle. Recommended when you have continuous web jobs running', **enum_choice_list(two_states_switch))
register_cli_argument('webapp config set', 'auto_heal_enabled', help='enable or disable auto heal', **enum_choice_list(two_states_switch))
register_cli_argument('webapp config set', 'use32_bit_worker_process', options_list=('--use-32bit-worker-process',), help='use 32 bits worker process or not', **enum_choice_list(two_states_switch))
register_cli_argument('webapp config set', 'php_version', help='The version used to run your web app if using PHP, e.g., 5.5, 5.6, 7.0')
register_cli_argument('webapp config set', 'python_version', help='The version used to run your web app if using Python, e.g., 2.7, 3.4')
register_cli_argument('webapp config set', 'net_framework_version', help="The version used to run your web app if using .NET Framework, e.g., 'v4.0' for .NET 4.6 and 'v3.0' for .NET 3.5")
register_cli_argument('webapp config set', 'linux_fx_version', help="The runtime stack used for your linux-based webapp, e.g., \"RUBY|2.3\", \"NODE|6.6\", \"PHP|5.6\", \"DOTNETCORE|1.1.0\". See https://aka.ms/linux-stacks for more info.")
register_cli_argument('webapp config set', 'java_version', help="The version used to run your web app if using Java, e.g., '1.7' for Java 7, '1.8' for Java 8")
register_cli_argument('webapp config set', 'java_container', help="The java container, e.g., Tomcat, Jetty")
register_cli_argument('webapp config set', 'java_container_version', help="The version of the java container, e.g., '8.0.23' for Tomcat")
register_cli_argument('webapp config set', 'app_command_line', options_list=('--startup-file',), help="The startup file for linux hosted web apps, e.g. 'process.json' for Node.js web")

register_cli_argument('webapp config backup', 'storage_account_url', help='URL with SAS token to the blob storage container', options_list=['--container-url'])
register_cli_argument('webapp config backup', 'webapp_name', help='The name of the webapp')
register_cli_argument('webapp config backup', 'db_name', help='Name of the database in the backup', arg_group='Database')
register_cli_argument('webapp config backup', 'db_connection_string', help='Connection string for the database in the backup', arg_group='Database')
register_cli_argument('webapp config backup', 'db_type', help='Type of database in the backup', arg_group='Database', **enum_choice_list(DatabaseType))

register_cli_argument('webapp config backup create', 'backup_name', help='Name of the backup. If unspecified, the backup will be named with the webapp name and a timestamp')

register_cli_argument('webapp config backup update', 'frequency', help='How often to backup. Use a number followed by d or h, e.g. 5d = 5 days, 2h = 2 hours')
register_cli_argument('webapp config backup update', 'keep_at_least_one_backup', help='Always keep one backup, regardless of how old it is', options_list=['--retain-one'], **enum_choice_list(two_states_switch))
register_cli_argument('webapp config backup update', 'retention_period_in_days', help='How many days to keep a backup before automatically deleting it. Set to 0 for indefinite retention', options_list=['--retention'])

register_cli_argument('webapp config backup restore', 'backup_name', help='Name of the backup to restore')
register_cli_argument('webapp config backup restore', 'target_name', help='The name to use for the restored webapp. If unspecified, will default to the name that was used when the backup was created')
register_cli_argument('webapp config backup restore', 'overwrite', help='Overwrite the source webapp, if --target-name is not specified', action='store_true')
register_cli_argument('webapp config backup restore', 'ignore_hostname_conflict', help='Ignores custom hostnames stored in the backup', action='store_true')

# end of new ones

# start of old ones #
register_cli_argument('appservice web', 'slot', options_list=('--slot', '-s'), help="the name of the slot. Default to the productions slot if not specified")
register_cli_argument('appservice web', 'name', configured_default='web',
                      arg_type=name_arg_type, completer=get_resource_name_completion_list('Microsoft.Web/sites'), id_part='name',
                      help="name of the web. You can configure the default using 'az configure --defaults web=<name>'")
register_cli_argument('appservice web create', 'name', options_list=('--name', '-n'), help='name of the new webapp')
register_cli_argument('appservice web create', 'deployment_local_git', action='store_true', options_list=('--deployment-local-git', '-l'), help='enable local git')
register_cli_argument('appservice web create', 'deployment_source_url', options_list=('--deployment-source-url', '-u'), help='Git repository URL to link with manual integration')
register_cli_argument('appservice web create', 'deployment_source_branch', options_list=('--deployment-source-branch', '-b'), help='the branch to deploy')
register_cli_argument('appservice web create', 'deployment_container_image_name', options_list=('--deployment-container-image-name', '-i'),
                      help='Linux only. Container image name from Docker Hub, e.g. publisher/image-name:version')
register_cli_argument('appservice web create', 'startup_file', help="Linux only. The web's startup file")
register_cli_argument('appservice web create', 'runtime', options_list=('--runtime', '-r'), help='canonicalized web runtime in the format of Framework|Version. For example, PHP|5.6')  # TODO ADD completer
register_cli_argument('appservice web list-runtimes', 'linux', action='store_true', help='list runtime stacks for linux based webapps')  # TODO ADD completer

register_cli_argument('appservice web create', 'plan', options_list=('--plan', '-p'), completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                      help="name or resource id of the app service plan. Use 'appservice plan create' to get one")

register_cli_argument('appservice web browse', 'logs', options_list=('--logs', '-l'), action='store_true', help='Enable viewing the log stream immediately after launching the web app')

register_cli_argument('appservice web deployment user', 'user_name', help='user name')
register_cli_argument('appservice web deployment user', 'password', help='password, will prompt if not specified')

register_cli_argument('appservice web deployment slot', 'slot', help='the name of the slot')
register_cli_argument('appservice web deployment slot', 'webapp', arg_type=name_arg_type, completer=get_resource_name_completion_list('Microsoft.Web/sites'),
                      help='Name of the webapp', id_part='name')
register_cli_argument('appservice web deployment slot', 'auto_swap_slot', help='target slot to auto swap', default='production')
register_cli_argument('appservice web deployment slot', 'disable', help='disable auto swap', action='store_true')
register_cli_argument('appservice web deployment slot', 'target_slot', help="target slot to swap, default to 'production'")
register_cli_argument('appservice web deployment slot create', 'configuration_source', help="source slot to clone configurations from. Use webapp's name to refer to the production slot")
register_cli_argument('appservice web deployment slot swap', 'action', help="swap types. use 'preview' to apply target slot's settings on the source slot first; use 'swap' to complete it; use 'reset' to reset the swap",
                      **enum_choice_list(['swap', 'preview', 'reset']))
register_cli_argument('appservice web log config', 'application_logging', help='configure application logging to file system', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web log config', 'detailed_error_messages', help='configure detailed error messages', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web log config', 'failed_request_tracing', help='configure failed request tracing', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web log config', 'level', help='logging level', **enum_choice_list(['error', 'warning', 'information', 'verbose']))
server_log_switch_options = ['off', 'storage', 'filesystem']
register_cli_argument('appservice web log config', 'web_server_logging', help='configure Web server logging', **enum_choice_list(server_log_switch_options))

register_cli_argument('appservice web log tail', 'provider', help="scope the live traces to certain providers/folders, for example:'application', 'http' for server log, 'kudu/trace', etc")
register_cli_argument('appservice web log download', 'log_file', default='webapp_logs.zip', type=file_type, completer=FilesCompleter(), help='the downloaded zipped log file path')

register_cli_argument('appservice web config appsettings', 'settings', nargs='+', help='space separated appsettings in a format of <name>=<value>')
register_cli_argument('appservice web config appsettings', 'slot_settings', nargs='+', help='space separated slot appsettings in a format of <name>=<value>')
register_cli_argument('appservice web config appsettings', 'setting_names', nargs='+', help='space separated sppsettings names')

register_cli_argument('appservice web config container', 'docker_registry_server_url', options_list=('--docker-registry-server-url', '-r'), help='the container registry server url')
register_cli_argument('appservice web config container', 'docker_custom_image_name', options_list=('--docker-custom-image-name', '-c'), help='the container custom image name and optionally the tag name')
register_cli_argument('appservice web config container', 'docker_registry_server_user', options_list=('--docker-registry-server-user', '-u'), help='the container registry server username')
register_cli_argument('appservice web config container', 'docker_registry_server_password', options_list=('--docker-registry-server-password', '-p'), help='the container registry server password')

register_cli_argument('appservice web config update', 'remote_debugging_enabled', help='enable or disable remote debugging', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web config update', 'web_sockets_enabled', help='enable or disable web sockets', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web config update', 'always_on', help='ensure webapp gets loaded all the time, rather unloaded after been idle. Recommended when you have continuous web jobs running', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web config update', 'auto_heal_enabled', help='enable or disable auto heal', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web config update', 'use32_bit_worker_process', options_list=('--use-32bit-worker-process',), help='use 32 bits worker process or not', **enum_choice_list(two_states_switch))
register_cli_argument('appservice web config update', 'php_version', help='The version used to run your web app if using PHP, e.g., 5.5, 5.6, 7.0')
register_cli_argument('appservice web config update', 'python_version', help='The version used to run your web app if using Python, e.g., 2.7, 3.4')
register_cli_argument('appservice web config update', 'net_framework_version', help="The version used to run your web app if using .NET Framework, e.g., 'v4.0' for .NET 4.6 and 'v3.0' for .NET 3.5")
register_cli_argument('appservice web config update', 'linux_fx_version', help="The runtime stack used for your linux-based webapp, e.g., \"RUBY|2.3\", \"NODE|6.6\", \"PHP|5.6\", \"DOTNETCORE|1.1.0\". See https://aka.ms/linux-stacks for more info.")
register_cli_argument('appservice web config update', 'java_version', help="The version used to run your web app if using Java, e.g., '1.7' for Java 7, '1.8' for Java 8")
register_cli_argument('appservice web config update', 'java_container', help="The java container, e.g., Tomcat, Jetty")
register_cli_argument('appservice web config update', 'java_container_version', help="The version of the java container, e.g., '8.0.23' for Tomcat")
register_cli_argument('appservice web config update', 'app_command_line', options_list=('--startup-file',), help="The startup file for linux hosted web apps, e.g. 'process.json' for Node.js web")

register_cli_argument('appservice web config ssl bind', 'ssl_type', help='The ssl cert type', **enum_choice_list(['SNI', 'IP']))
register_cli_argument('appservice web config ssl upload', 'certificate_password', help='The ssl cert password')
register_cli_argument('appservice web config ssl upload', 'certificate_file', type=file_type, help='The filepath for the .pfx file')
register_cli_argument('appservice web config ssl', 'certificate_thumbprint', help='The ssl cert thumbprint')

register_cli_argument('appservice web config hostname', 'webapp_name', help="webapp name. You can configure the default using 'az configure --defaults web=<name>'", configured_default='web',
                      completer=get_resource_name_completion_list('Microsoft.Web/sites'), id_part='name')
register_cli_argument('appservice web config hostname', 'hostname', completer=get_hostname_completion_list, help="hostname assigned to the site, such as custom domains", id_part='child_name')

register_cli_argument('appservice web config backup', 'storage_account_url', help='URL with SAS token to the blob storage container', options_list=['--container-url'])
register_cli_argument('appservice web config backup', 'webapp_name', help='The name of the webapp')
register_cli_argument('appservice web config backup', 'db_name', help='Name of the database in the backup', arg_group='Database')
register_cli_argument('appservice web config backup', 'db_connection_string', help='Connection string for the database in the backup', arg_group='Database')
register_cli_argument('appservice web config backup', 'db_type', help='Type of database in the backup', arg_group='Database', **enum_choice_list(DatabaseType))

register_cli_argument('appservice web config backup create', 'backup_name', help='Name of the backup. If unspecified, the backup will be named with the webapp name and a timestamp')

register_cli_argument('appservice web config backup update', 'frequency', help='How often to backup. Use a number followed by d or h, e.g. 5d = 5 days, 2h = 2 hours')
register_cli_argument('appservice web config backup update', 'keep_at_least_one_backup', help='Always keep one backup, regardless of how old it is', options_list=['--retain-one'], **enum_choice_list(two_states_switch))
register_cli_argument('appservice web config backup update', 'retention_period_in_days', help='How many days to keep a backup before automatically deleting it. Set to 0 for indefinite retention', options_list=['--retention'])

register_cli_argument('appservice web config backup restore', 'backup_name', help='Name of the backup to restore')
register_cli_argument('appservice web config backup restore', 'target_name', help='The name to use for the restored webapp. If unspecified, will default to the name that was used when the backup was created')
register_cli_argument('appservice web config backup restore', 'overwrite', help='Overwrite the source webapp, if --target-name is not specified', action='store_true')
register_cli_argument('appservice web config backup restore', 'ignore_hostname_conflict', help='Ignores custom hostnames stored in the backup', action='store_true')

register_cli_argument('appservice web source-control', 'manual_integration', action='store_true', help='disable automatic sync between source control and web')
register_cli_argument('appservice web source-control', 'repo_url', help='repository url to pull the latest source from, e.g. https://github.com/foo/foo-web')
register_cli_argument('appservice web source-control', 'branch', help='the branch name of the repository')
register_cli_argument('appservice web source-control', 'cd_provider', help='type of CI/CD provider', default='kudu', **enum_choice_list(['kudu', 'vsts']))
register_cli_argument('appservice web source-control', 'cd_app_type', arg_group='VSTS CD Provider', help='web application framework you used to develop your app', default='AspNetWap', **enum_choice_list(['AspNetWap', 'AspNetCore', 'NodeJSWithGulp', 'NodeJSWithGrunt']))
register_cli_argument('appservice web source-control', 'cd_account', arg_group='VSTS CD Provider', help='name of the Team Services account to create/use for continuous delivery')
register_cli_argument('appservice web source-control', 'cd_account_must_exist', arg_group='VSTS CD Provider', help='specifies that the account must already exist. If not specified, the account will be created if it does not already exist (existing accounts are updated)', action='store_true')
register_cli_argument('appservice web source-control', 'repository_type', help='repository type', default='git', **enum_choice_list(['git', 'mercurial']))
register_cli_argument('appservice web source-control', 'git_token', help='git access token required for auto sync')
# end of olds ones #

register_cli_argument('functionapp', 'name', arg_type=name_arg_type, id_part='name', help='name of the function app')
register_cli_argument('functionapp config hostname', 'webapp_name', arg_type=name_arg_type, id_part='name', help='name of the function app')
register_cli_argument('functionapp create', 'plan', options_list=('--plan', '-p'), completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                      help="name or resource id of the function app service plan. Use 'appservice plan create' to get one")
register_cli_argument('functionapp create', 'new_app_name', options_list=('--name', '-n'), help='name of the new function app')
register_cli_argument('functionapp create', 'storage_account', options_list=('--storage-account', '-s'),
                      help='Provide a string value of a Storage Account in the provided Resource Group. Or Resource ID of a Storage Account in a different Resource Group')

# For commands with shared impl between webapp and functionapp and has output, we apply type validation to avoid confusions
register_cli_argument('appservice web show', 'name', arg_type=webapp_name_arg_type, validator=validate_existing_web_app)
register_cli_argument('webapp show', 'name', arg_type=webapp_name_arg_type, validator=validate_existing_web_app)
register_cli_argument('functionapp show', 'name', arg_type=name_arg_type, validator=validate_existing_function_app)

register_cli_argument('functionapp', 'name', arg_type=name_arg_type, id_part='name', help="name of the function")
register_cli_argument('functionapp create', 'plan', options_list=('--plan', '-p'), completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                      help="name or resource id of the function app service plan. Use 'appservice plan create' to get one")
register_cli_argument('functionapp create', 'consumption_plan_location', options_list=('--consumption-plan-location', '-c'),
                      help="Geographic location where Function App will be hosted. Use 'functionapp list-consumption-locations' to view available locations.")
register_cli_argument('functionapp create', 'storage_account', options_list=('--storage-account', '-s'),
                      help='Provide a string value of a Storage Account in the provided Resource Group. Or Resource ID of a Storage Account in a different Resource Group')
