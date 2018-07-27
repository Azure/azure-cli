# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from argcomplete.completers import FilesCompleter

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (resource_group_name_type, get_location_type,
                                                get_resource_name_completion_list, file_type,
                                                get_three_state_flag, get_enum_type)
from azure.mgmt.web.models import DatabaseType, ConnectionStringType, BuiltInAuthenticationProvider

from ._completers import get_hostname_completion_list

AUTH_TYPES = {
    'AllowAnonymous': 'na',
    'LoginWithAzureActiveDirectory': BuiltInAuthenticationProvider.azure_active_directory,
    'LoginWithFacebook': BuiltInAuthenticationProvider.facebook,
    'LoginWithGoogle': BuiltInAuthenticationProvider.google,
    'LoginWithMicrosoftAccount': BuiltInAuthenticationProvider.microsoft_account,
    'LoginWithTwitter': BuiltInAuthenticationProvider.twitter}

MULTI_CONTAINER_TYPES = ['COMPOSE', 'KUBE']

# pylint: disable=too-many-statements


def load_arguments(self, _):

    # pylint: disable=line-too-long
    # PARAMETER REGISTRATION
    name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME')
    sku_arg_type = CLIArgumentType(help='The pricing tiers, e.g., F1(Free), D1(Shared), B1(Basic Small), B2(Basic Medium), B3(Basic Large), S1(Standard Small), P1(Premium Small), P1V2(Premium V2 Small) etc',
                                   arg_type=get_enum_type(['F1', 'FREE', 'D1', 'SHARED', 'B1', 'B2', 'B3', 'S1', 'S2', 'S3', 'P1', 'P2', 'P3', 'P1V2', 'P2V2', 'P3V2']))
    webapp_name_arg_type = CLIArgumentType(configured_default='web', options_list=['--name', '-n'], metavar='NAME',
                                           completer=get_resource_name_completion_list('Microsoft.Web/sites'), id_part='name',
                                           help="name of the web. You can configure the default using 'az configure --defaults web=<name>'")

    # use this hidden arg to give a command the right instance, that functionapp commands
    # work on function app and webapp ones work on web app
    with self.argument_context('webapp') as c:
        c.ignore('app_instance')
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('slot', options_list=['--slot', '-s'], help="the name of the slot. Default to the productions slot if not specified")
        c.argument('name', configured_default='web', arg_type=name_arg_type,
                   completer=get_resource_name_completion_list('Microsoft.Web/sites'), id_part='name',
                   help="name of the web. You can configure the default using 'az configure --defaults web=<name>'")

    with self.argument_context('appservice') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('location', arg_type=get_location_type(self.cli_ctx))

    with self.argument_context('appservice list-locations') as c:
        c.argument('linux_workers_enabled', action='store_true', help='get regions which support hosting webapps on Linux workers')
        c.argument('sku', arg_type=sku_arg_type)

    with self.argument_context('appservice plan') as c:
        c.argument('name', arg_type=name_arg_type, help='The name of the app service plan',
                   completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                   configured_default='appserviceplan', id_part='name')
        c.argument('number_of_workers', help='Number of workers to be allocated.', type=int, default=1)
        c.argument('admin_site_name', help='The name of the admin web app.')

    with self.argument_context('appservice plan create') as c:
        c.argument('name', options_list=['--name', '-n'], help="Name of the new app service plan", completer=None)
        c.argument('sku', arg_type=sku_arg_type)
        c.argument('is_linux', action='store_true', required=False, help='host webapp on Linux worker')
    with self.argument_context('appservice plan update') as c:
        c.argument('sku', arg_type=sku_arg_type)
        c.ignore('allow_pending_state')

    with self.argument_context('webapp create') as c:
        c.argument('name', options_list=['--name', '-n'], help='name of the new webapp')
        c.argument('startup_file', help="Linux only. The web's startup file")
        c.argument('multicontainer_config_type', options_list=['--multicontainer-config-type'], help="Linux only.", arg_type=get_enum_type(MULTI_CONTAINER_TYPES))
        c.argument('multicontainer_config_file', options_list=['--multicontainer-config-file'], help="Linux only. Config file for multicontainer apps. (local or remote)")
        c.argument('runtime', options_list=['--runtime', '-r'], help="canonicalized web runtime in the format of Framework|Version, e.g. \"PHP|5.6\". Use 'az webapp list-runtimes' for available list")  # TODO ADD completer
        c.argument('plan', options_list=['--plan', '-p'], configured_default='appserviceplan',
                   completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                   help="name or resource id of the app service plan. Use 'appservice plan create' to get one")

    with self.argument_context('webapp show') as c:
        c.argument('name', arg_type=webapp_name_arg_type)

    with self.argument_context('webapp list-runtimes') as c:
        c.argument('linux', action='store_true', help='list runtime stacks for linux based webapps')

    with self.argument_context('webapp traffic-routing') as c:
        c.argument('distribution', options_list=['--distribution', '-d'], nargs='+', help='space-separated slot routings in a format of <slot-name>=<percentage> e.g. staging=50. Unused traffic percentage will go to the Production slot')

    with self.argument_context('webapp update') as c:
        c.argument('client_affinity_enabled', help="Enables sending session affinity cookies.", arg_type=get_three_state_flag(return_label=True))
        c.argument('https_only', help="Redirect all traffic made to an app using HTTP to HTTPS.", arg_type=get_three_state_flag(return_label=True))
        c.argument('force_dns_registration', help="If true, web app hostname is force registered with DNS", arg_type=get_three_state_flag(return_label=True))
        c.argument('skip_custom_domain_verification', help="If true, custom (non *.azurewebsites.net) domains associated with web app are not verified", arg_type=get_three_state_flag(return_label=True))
        c.argument('ttl_in_seconds', help="Time to live in seconds for web app's default domain name", arg_type=get_three_state_flag(return_label=True))
        c.argument('skip_dns_registration', help="If true web app hostname is not registered with DNS on creation", arg_type=get_three_state_flag(return_label=True))

    with self.argument_context('webapp browse') as c:
        c.argument('logs', options_list=['--logs', '-l'], action='store_true', help='Enable viewing the log stream immediately after launching the web app')
    with self.argument_context('webapp delete') as c:
        c.argument('keep_empty_plan', action='store_true', help='keep empty app service plan')
        c.argument('keep_metrics', action='store_true', help='keep app metrics')
        c.argument('keep_dns_registration', action='store_true', help='keep DNS registration')

    for scope in ['webapp', 'functionapp']:
        with self.argument_context(scope + ' create') as c:
            c.argument('deployment_container_image_name', options_list=['--deployment-container-image-name', '-i'], help='Linux only. Container image name from Docker Hub, e.g. publisher/image-name:tag')
            c.argument('deployment_local_git', action='store_true', options_list=['--deployment-local-git', '-l'], help='enable local git')
            c.argument('deployment_zip', options_list=['--deployment-zip', '-z'], help='perform deployment using zip file')
            c.argument('deployment_source_url', options_list=['--deployment-source-url', '-u'], help='Git repository URL to link with manual integration')
            c.argument('deployment_source_branch', options_list=['--deployment-source-branch', '-b'], help='the branch to deploy')
        with self.argument_context(scope + ' config ssl bind') as c:
            c.argument('ssl_type', help='The ssl cert type', arg_type=get_enum_type(['SNI', 'IP']))
        with self.argument_context(scope + ' config ssl upload') as c:
            c.argument('certificate_password', help='The ssl cert password')
            c.argument('certificate_file', type=file_type, help='The filepath for the .pfx file')
        with self.argument_context(scope + ' config ssl') as c:
            c.argument('certificate_thumbprint', help='The ssl cert thumbprint')
        with self.argument_context(scope + ' config appsettings') as c:
            c.argument('settings', nargs='+', help="space-separated app settings in a format of <name>=<value>")
            c.argument('setting_names', nargs='+', help="space-separated app setting names")

        with self.argument_context(scope + ' config hostname') as c:
            c.argument('hostname', completer=get_hostname_completion_list, help="hostname assigned to the site, such as custom domains", id_part='child_name_1')
        with self.argument_context(scope + ' deployment user') as c:
            c.argument('user_name', help='user name')
            c.argument('password', help='password, will prompt if not specified')
        with self.argument_context(scope + ' deployment source') as c:
            c.argument('manual_integration', action='store_true', help='disable automatic sync between source control and web')
            c.argument('repo_url', options_list=['--repo-url', '-u'], help='repository url to pull the latest source from, e.g. https://github.com/foo/foo-web')
            c.argument('branch', help='the branch name of the repository')
            c.argument('private_repo_username', arg_group='VSTS CD Provider', help='Username for the private repository')
            c.argument('private_repo_password', arg_group='VSTS CD Provider', help='Password for the private repository')
            c.argument('cd_app_type', arg_group='VSTS CD Provider', help='Web application framework you used to develop your app. Default is AspNet.', arg_type=get_enum_type(['AspNet', 'AspNetCore', 'NodeJS', 'PHP', 'Python']))
            c.argument('app_working_dir', arg_group='VSTS CD Provider', help='Working directory of the application. Default will be root of the repo')
            c.argument('nodejs_task_runner', arg_group='VSTS CD Provider', help='Task runner for nodejs. Default is None', arg_type=get_enum_type(['None', 'Gulp', 'Grunt']))
            c.argument('python_framework', arg_group='VSTS CD Provider', help='Framework used for Python application. Default is Django', arg_type=get_enum_type(['Bottle', 'Django', 'Flask']))
            c.argument('python_version', arg_group='VSTS CD Provider', help='Python version used for application. Default is Python 3.5.3 x86', arg_type=get_enum_type(['Python 2.7.12 x64', 'Python 2.7.12 x86', 'Python 2.7.13 x64', 'Python 2.7.13 x86', 'Python 3.5.3 x64', 'Python 3.5.3 x86', 'Python 3.6.0 x64', 'Python 3.6.0 x86', 'Python 3.6.2 x64', 'Python 3.6.1 x86']))
            c.argument('cd_project_url', arg_group='VSTS CD Provider', help='URL of the Visual Studio Team Services (VSTS) project to use for continuous delivery. URL should be in format https://<accountname>.visualstudio.com/<projectname>')
            c.argument('cd_account_create', arg_group='VSTS CD Provider', help="To create a new Visual Studio Team Services (VSTS) account if it doesn't exist already", action='store_true')
            c.argument('test', arg_group='VSTS CD Provider', help='Name of the web app to be used for load testing. If web app is not available, it will be created. Default: Disable')
            c.argument('slot_swap', arg_group='VSTS CD Provider', help='Name of the slot to be used for deployment and later promote to production. If slot is not available, it will be created. Default: Not configured')
            c.argument('repository_type', help='repository type', arg_type=get_enum_type(['git', 'mercurial', 'vsts', 'github', 'externalgit', 'localgit']))
            c.argument('git_token', help='Git access token required for auto sync')
        with self.argument_context(scope + ' identity') as c:
            c.argument('scope', help="The scope the managed identity has access to")
            c.argument('role', help="Role name or id the managed identity will be assigned")

        with self.argument_context(scope + ' deployment source config-zip') as c:
            c.argument('src', help='a zip file path for deployment')

        with self.argument_context(scope + ' config appsettings list') as c:
            c.argument('name', arg_type=webapp_name_arg_type, id_part=None)

        with self.argument_context(scope + ' config hostname list') as c:
            c.argument('webapp_name', arg_type=webapp_name_arg_type, id_part=None, options_list='--webapp-name')

    with self.argument_context('webapp config connection-string list') as c:
        c.argument('name', arg_type=webapp_name_arg_type, id_part=None)

    with self.argument_context('webapp config hostname') as c:
        c.argument('webapp_name', help="webapp name. You can configure the default using 'az configure --defaults web=<name>'", configured_default='web',
                   completer=get_resource_name_completion_list('Microsoft.Web/sites'), id_part='name')
    with self.argument_context('webapp deployment container config') as c:
        c.argument('enable', options_list=['--enable-cd', '-e'], help='enable/disable continuous deployment', arg_type=get_enum_type(['true', 'false']))
    with self.argument_context('webapp deployment slot') as c:
        c.argument('slot', help='the name of the slot')
        c.argument('webapp', arg_type=name_arg_type, completer=get_resource_name_completion_list('Microsoft.Web/sites'),
                   help='Name of the webapp', id_part='name')
        c.argument('auto_swap_slot', help='target slot to auto swap', default='production')
        c.argument('disable', help='disable auto swap', action='store_true')
        c.argument('target_slot', help="target slot to swap, default to 'production'")
    with self.argument_context('webapp deployment slot create') as c:
        c.argument('configuration_source', help="source slot to clone configurations from. Use webapp's name to refer to the production slot")
    with self.argument_context('webapp deployment slot swap') as c:
        c.argument('action', help="swap types. use 'preview' to apply target slot's settings on the source slot first; use 'swap' to complete it; use 'reset' to reset the swap",
                   arg_type=get_enum_type(['swap', 'preview', 'reset']))
    with self.argument_context('webapp log config') as c:
        c.argument('application_logging', help='configure application logging to file system', arg_type=get_three_state_flag(return_label=True))
        c.argument('detailed_error_messages', help='configure detailed error messages', arg_type=get_three_state_flag(return_label=True))
        c.argument('failed_request_tracing', help='configure failed request tracing', arg_type=get_three_state_flag(return_label=True))
        c.argument('level', help='logging level', arg_type=get_enum_type(['error', 'warning', 'information', 'verbose']))
        c.argument('web_server_logging', help='configure Web server logging', arg_type=get_enum_type(['off', 'filesystem']))
        c.argument('docker_container_logging', help='configure gathering STDOUT and STDERR output from container', arg_type=get_enum_type(['off', 'filesystem']))

    with self.argument_context('webapp log tail') as c:
        c.argument('provider', help="By default all live traces configured by 'az webapp log config' will be shown, but you can scope to certain providers/folders, e.g. 'application', 'http', etc. For details, check out https://github.com/projectkudu/kudu/wiki/Diagnostic-Log-Stream")
    with self.argument_context('webapp log download') as c:
        c.argument('log_file', default='webapp_logs.zip', type=file_type, completer=FilesCompleter(), help='the downloaded zipped log file path')

    for scope in ['appsettings', 'connection-string']:
        with self.argument_context('webapp config ' + scope) as c:
            c.argument('settings', nargs='+', help="space-separated {} in a format of <name>=<value>".format(scope))
            c.argument('slot_settings', nargs='+', help="space-separated slot {} in a format of <name>=<value>".format(scope))
            c.argument('setting_names', nargs='+', help="space-separated {} names".format(scope))

    with self.argument_context('webapp config connection-string') as c:
        c.argument('connection_string_type', options_list=['--connection-string-type', '-t'], help='connection string type', arg_type=get_enum_type(ConnectionStringType))

    with self.argument_context('webapp config container') as c:
        c.argument('docker_registry_server_url', options_list=['--docker-registry-server-url', '-r'], help='the container registry server url')
        c.argument('docker_custom_image_name', options_list=['--docker-custom-image-name', '-c', '-i'], help='the container custom image name and optionally the tag name')
        c.argument('docker_registry_server_user', options_list=['--docker-registry-server-user', '-u'], help='the container registry server username')
        c.argument('docker_registry_server_password', options_list=['--docker-registry-server-password', '-p'], help='the container registry server password')
        c.argument('websites_enable_app_service_storage', options_list=['--enable-app-service-storage', '-t'], help='enables platform storage (custom container only)', arg_type=get_three_state_flag(return_label=True))
        c.argument('multicontainer_config_type', options_list=['--multicontainer-config-type'], help='config type', arg_type=get_enum_type(MULTI_CONTAINER_TYPES))
        c.argument('multicontainer_config_file', options_list=['--multicontainer-config-file'], help="config file for multicontainer apps")
        c.argument('show_multicontainer_config', action='store_true', help='shows decoded config if a multicontainer config is set')

    with self.argument_context('webapp config set') as c:
        c.argument('remote_debugging_enabled', help='enable or disable remote debugging', arg_type=get_three_state_flag(return_label=True))
        c.argument('web_sockets_enabled', help='enable or disable web sockets', arg_type=get_three_state_flag(return_label=True))
        c.argument('always_on', help='ensure webapp gets loaded all the time, rather unloaded after been idle. Recommended when you have continuous web jobs running', arg_type=get_three_state_flag(return_label=True))
        c.argument('auto_heal_enabled', help='enable or disable auto heal', arg_type=get_three_state_flag(return_label=True))
        c.argument('use32_bit_worker_process', options_list=['--use-32bit-worker-process'], help='use 32 bits worker process or not', arg_type=get_three_state_flag(return_label=True))
        c.argument('php_version', help='The version used to run your web app if using PHP, e.g., 5.5, 5.6, 7.0')
        c.argument('python_version', help='The version used to run your web app if using Python, e.g., 2.7, 3.4')
        c.argument('net_framework_version', help="The version used to run your web app if using .NET Framework, e.g., 'v4.0' for .NET 4.6 and 'v3.0' for .NET 3.5")
        c.argument('linux_fx_version', help="The runtime stack used for your linux-based webapp, e.g., \"RUBY|2.3\", \"NODE|6.6\", \"PHP|5.6\", \"DOTNETCORE|1.1.0\". See https://aka.ms/linux-stacks for more info.")
        c.argument('java_version', help="The version used to run your web app if using Java, e.g., '1.7' for Java 7, '1.8' for Java 8")
        c.argument('java_container', help="The java container, e.g., Tomcat, Jetty")
        c.argument('java_container_version', help="The version of the java container, e.g., '8.0.23' for Tomcat")
        c.argument('min_tls_version', help="The minimum version of TLS required for SSL requests, e.g., '1.0', '1.1', '1.2'")
        c.argument('http20_enabled', help="configures a web site to allow clients to connect over http2.0.", arg_type=get_three_state_flag(return_label=True))
        c.argument('app_command_line', options_list=['--startup-file'], help="The startup file for linux hosted web apps, e.g. 'process.json' for Node.js web")

    with self.argument_context('webapp config backup') as c:
        c.argument('storage_account_url', help='URL with SAS token to the blob storage container', options_list=['--container-url'])
        c.argument('webapp_name', help='The name of the webapp')
        c.argument('db_name', help='Name of the database in the backup', arg_group='Database')
        c.argument('db_connection_string', help='Connection string for the database in the backup', arg_group='Database')
        c.argument('db_type', help='Type of database in the backup', arg_group='Database', arg_type=get_enum_type(DatabaseType))

    with self.argument_context('webapp config backup create') as c:
        c.argument('backup_name', help='Name of the backup. If unspecified, the backup will be named with the webapp name and a timestamp')

    with self.argument_context('webapp config backup update') as c:
        c.argument('backup_name', help='Name of the backup. If unspecified, the backup will be named with the webapp name and a timestamp')
        c.argument('frequency', help='How often to backup. Use a number followed by d or h, e.g. 5d = 5 days, 2h = 2 hours')
        c.argument('keep_at_least_one_backup', help='Always keep one backup, regardless of how old it is', options_list=['--retain-one'], arg_type=get_three_state_flag(return_label=True))
        c.argument('retention_period_in_days', help='How many days to keep a backup before automatically deleting it. Set to 0 for indefinite retention', options_list=['--retention'])

    with self.argument_context('webapp config backup restore') as c:
        c.argument('backup_name', help='Name of the backup to restore')
        c.argument('target_name', help='The name to use for the restored webapp. If unspecified, will default to the name that was used when the backup was created')
        c.argument('overwrite', help='Overwrite the source webapp, if --target-name is not specified', action='store_true')
        c.argument('ignore_hostname_conflict', help='Ignores custom hostnames stored in the backup', action='store_true')

    with self.argument_context('webapp auth update') as c:
        c.argument('enabled', arg_type=get_three_state_flag(return_label=True))
        c.argument('token_store_enabled', options_list=['--token-store'], arg_type=get_three_state_flag(return_label=True), help='use App Service Token Store')
        c.argument('action', arg_type=get_enum_type(AUTH_TYPES))
        c.argument('runtime_version', help='Runtime version of the Authentication/Authorization feature in use for the current app')
        c.argument('token_refresh_extension_hours', type=float, help="Hours, must be formattable into a float")
        c.argument('allowed_external_redirect_urls', nargs='+', help="One or more urls (space-delimited).")
        c.argument('client_id', options_list=['--aad-client-id'], arg_group='Azure Active Directory', help='Application ID to integrate AAD organization account Sign-in into your web app')
        c.argument('client_secret', options_list=['--aad-client-secret'], arg_group='Azure Active Directory', help='AAD application secret')
        c.argument('allowed_audiences', nargs='+', options_list=['--aad-allowed-token-audiences'], arg_group='Azure Active Directory', help="One or more token audiences (space-delimited).")
        c.argument('issuer', options_list=['--aad-token-issuer-url'],
                   help='This url can be found in the JSON output returned from your active directory endpoint using your tenantID. The endpoint can be queried from \'az cloud show\' at \"endpoints.activeDirectory\". '
                        'The tenantID can be found using \'az account show\'. Get the \"issuer\" from the JSON at <active directory endpoint>/<tenantId>/.well-known/openid-configuration.', arg_group='Azure Active Directory')
        c.argument('facebook_app_id', arg_group='Facebook', help="Application ID to integrate Facebook Sign-in into your web app")
        c.argument('facebook_app_secret', arg_group='Facebook', help='Facebook Application client secret')
        c.argument('facebook_oauth_scopes', nargs='+', help="One or more facebook authentication scopes (space-delimited).", arg_group='Facebook')
        c.argument('twitter_consumer_key', arg_group='Twitter', help='Application ID to integrate Twitter Sign-in into your web app')
        c.argument('twitter_consumer_secret', arg_group='Twitter', help='Twitter Application client secret')
        c.argument('google_client_id', arg_group='Google', help='Application ID to integrate Google Sign-in into your web app')
        c.argument('google_client_secret', arg_group='Google', help='Google Application client secret')
        c.argument('google_oauth_scopes', nargs='+', help="One or more Google authentication scopes (space-delimited).", arg_group='Google')
        c.argument('microsoft_account_client_id', arg_group='Microsoft', help="AAD V2 Application ID to integrate Microsoft account Sign-in into your web app")
        c.argument('microsoft_account_client_secret', arg_group='Microsoft', help='AAD V2 Application client secret')
        c.argument('microsoft_account_oauth_scopes', nargs='+', help="One or more Microsoft authentification scopes (space-delimited).", arg_group='Microsoft')

    with self.argument_context('functionapp') as c:
        c.ignore('app_instance', 'slot')
        c.argument('name', arg_type=name_arg_type, id_part='name', help='name of the function app')
    with self.argument_context('functionapp config hostname') as c:
        c.argument('webapp_name', arg_type=name_arg_type, id_part='name', help='name of the function app')
    with self.argument_context('functionapp create') as c:
        c.argument('plan', options_list=['--plan', '-p'], configured_default='appserviceplan',
                   completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                   help="name or resource id of the function app service plan. Use 'appservice plan create' to get one")
        c.argument('new_app_name', options_list=['--name', '-n'], help='name of the new function app')
        c.argument('storage_account', options_list=['--storage-account', '-s'],
                   help='Provide a string value of a Storage Account in the provided Resource Group. Or Resource ID of a Storage Account in a different Resource Group')
        c.argument('consumption_plan_location', options_list=['--consumption-plan-location', '-c'],
                   help="Geographic location where Function App will be hosted. Use 'functionapp list-consumption-locations' to view available locations.")
    # For commands with shared impl between webapp and functionapp and has output, we apply type validation to avoid confusions
    with self.argument_context('functionapp show') as c:
        c.argument('name', arg_type=name_arg_type)
    with self.argument_context('functionapp config appsettings') as c:
        c.argument('slot_settings', nargs='+', help="space-separated slot app settings in a format of <name>=<value>")
