# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from argcomplete.completers import FilesCompleter

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (resource_group_name_type, get_location_type,
                                                get_resource_name_completion_list, file_type,
                                                get_three_state_flag, get_enum_type, tags_type)
from azure.cli.core.local_context import LocalContextAttribute, LocalContextAction
from azure.cli.command_modules.appservice._appservice_utils import MSI_LOCAL_ID
from azure.mgmt.web.models import DatabaseType, ConnectionStringType, BuiltInAuthenticationProvider, AzureStorageType

from ._completers import get_hostname_completion_list
from ._constants import (FUNCTIONS_VERSIONS, WINDOWS_OS_NAME, LINUX_OS_NAME)

from ._validators import (validate_timeout_value, validate_site_create, validate_asp_create,
                          validate_front_end_scale_factor, validate_ase_create, validate_ip_address,
                          validate_service_tag, validate_public_cloud)

AUTH_TYPES = {
    'AllowAnonymous': 'na',
    'LoginWithAzureActiveDirectory': BuiltInAuthenticationProvider.azure_active_directory,
    'LoginWithFacebook': BuiltInAuthenticationProvider.facebook,
    'LoginWithGoogle': BuiltInAuthenticationProvider.google,
    'LoginWithMicrosoftAccount': BuiltInAuthenticationProvider.microsoft_account,
    'LoginWithTwitter': BuiltInAuthenticationProvider.twitter}

MULTI_CONTAINER_TYPES = ['COMPOSE', 'KUBE']
FTPS_STATE_TYPES = ['AllAllowed', 'FtpsOnly', 'Disabled']
OS_TYPES = ['Windows', 'Linux']
ACCESS_RESTRICTION_ACTION_TYPES = ['Allow', 'Deny']
ASE_LOADBALANCER_MODES = ['Internal', 'External']
ASE_KINDS = ['ASEv2', 'ASEv3']
ASE_OS_PREFERENCE_TYPES = ['Windows', 'Linux']


# pylint: disable=too-many-statements, too-many-lines


def load_arguments(self, _):
    # pylint: disable=line-too-long
    # PARAMETER REGISTRATION
    name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME')
    sku_arg_type = CLIArgumentType(
        help='The pricing tiers, e.g., F1(Free), D1(Shared), B1(Basic Small), B2(Basic Medium), B3(Basic Large), S1(Standard Small), P1V2(Premium V2 Small), P1V3(Premium V3 Small), P2V3(Premium V3 Medium), P3V3(Premium V3 Large), I1 (Isolated Small), I2 (Isolated Medium), I3 (Isolated Large), I1v2 (Isolated V2 Small), I2v2 (Isolated V2 Medium), I3v2 (Isolated V2 Large), WS1 (Logic Apps Workflow Standard 1), WS2 (Logic Apps Workflow Standard 2), WS3 (Logic Apps Workflow Standard 3)',
        arg_type=get_enum_type(
            ['F1', 'FREE', 'D1', 'SHARED', 'B1', 'B2', 'B3', 'S1', 'S2', 'S3', 'P1V2', 'P2V2', 'P3V2', 'P1V3', 'P2V3', 'P3V3', 'I1', 'I2', 'I3', 'I1v2', 'I2v2', 'I3v2', 'WS1', 'WS2', 'WS3']))
    webapp_name_arg_type = CLIArgumentType(configured_default='web', options_list=['--name', '-n'], metavar='NAME',
                                           completer=get_resource_name_completion_list('Microsoft.Web/sites'),
                                           id_part='name',
                                           help="name of the web app. If left unspecified, a name will be randomly generated. You can configure the default using `az configure --defaults web=<name>`",
                                           local_context_attribute=LocalContextAttribute(name='web_name', actions=[
                                               LocalContextAction.GET]))
    functionapp_name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME',
                                                help="name of the function app.",
                                                local_context_attribute=LocalContextAttribute(name='functionapp_name',
                                                                                              actions=[
                                                                                                  LocalContextAction.GET]))
    logicapp_name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME',
                                             help="name of the logic app.",
                                             local_context_attribute=LocalContextAttribute(name='logicapp_name',
                                                                                           actions=[LocalContextAction.GET]))
    name_arg_type_dict = {
        'functionapp': functionapp_name_arg_type,
        'logicapp': logicapp_name_arg_type
    }
    isolated_sku_arg_type = CLIArgumentType(
        help='The Isolated pricing tiers, e.g., I1 (Isolated Small), I2 (Isolated Medium), I3 (Isolated Large)',
        arg_type=get_enum_type(['I1', 'I2', 'I3']))

    static_web_app_sku_arg_type = CLIArgumentType(
        help='The pricing tiers for Static Web App',
        arg_type=get_enum_type(['Free', 'Standard'])
    )

    # use this hidden arg to give a command the right instance, that functionapp commands
    # work on function app and webapp ones work on web app
    with self.argument_context('webapp') as c:
        c.ignore('app_instance')
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('slot', options_list=['--slot', '-s'],
                   help="the name of the slot. Default to the productions slot if not specified")
        c.argument('name', arg_type=webapp_name_arg_type)

    with self.argument_context('appservice') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('location', arg_type=get_location_type(self.cli_ctx))

    with self.argument_context('appservice list-locations') as c:
        c.argument('linux_workers_enabled', action='store_true',
                   help='get regions which support hosting web apps on Linux workers')
        c.argument('sku', arg_type=sku_arg_type)

    with self.argument_context('appservice plan') as c:
        c.argument('name', arg_type=name_arg_type, help='The name of the app service plan',
                   completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                   configured_default='appserviceplan', id_part='name',
                   local_context_attribute=LocalContextAttribute(name='plan_name', actions=[LocalContextAction.GET]))
        c.argument('number_of_workers', help='Number of workers to be allocated.', type=int, default=1)
        c.ignore('max_burst')

    with self.argument_context('appservice plan create') as c:
        c.argument('name', options_list=['--name', '-n'], help="Name of the new app service plan", completer=None,
                   validator=validate_asp_create,
                   local_context_attribute=LocalContextAttribute(name='plan_name', actions=[LocalContextAction.SET],
                                                                 scopes=['appservice', 'webapp', 'functionapp']))
        c.argument('number_of_workers', help='Number of workers to be allocated.', type=int, default=1)
        c.argument('app_service_environment', options_list=['--app-service-environment', '-e'],
                   help="Name or ID of the app service environment",
                   local_context_attribute=LocalContextAttribute(name='ase_name', actions=[LocalContextAction.GET]))
        c.argument('sku', arg_type=sku_arg_type)
        c.argument('is_linux', action='store_true', required=False, help='host web app on Linux worker')
        c.argument('hyper_v', action='store_true', required=False, help='Host web app on Windows container')
        c.argument('per_site_scaling', action='store_true', required=False, help='Enable per-app scaling at the '
                                                                                 'App Service plan level to allow for '
                                                                                 'scaling an app independently from '
                                                                                 'the App Service plan that hosts it.')
        c.argument('zone_redundant', options_list=['--zone-redundant', '-z'], help='Enable zone redundancy for high availability. Cannot be changed after plan creation. Minimum instance count is 3.')
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('appservice plan update') as c:
        c.argument('sku', arg_type=sku_arg_type)
        c.argument('elastic_scale', arg_type=get_three_state_flag(), is_preview=True, help='Enable or disable automatic scaling. Set to "true" to enable elastic scale for this plan, or "false" to disable elastic scale for this plan. The SKU must be a Premium V2 SKU (P1V2, P2V2, P3V2) or a Premium V3 SKU (P1V3, P2V3, P3V3)')
        c.argument('max_elastic_worker_count', options_list=['--max-elastic-worker-count', '-m'], type=int, is_preview=True, help='Maximum number of instances that the plan can scale out to. The plan must be an elastic scale plan.')
        c.argument('number_of_workers', type=int, help='Number of workers to be allocated.')
        c.ignore('allow_pending_state')

    with self.argument_context('appservice plan delete') as c:
        c.argument('name', arg_type=name_arg_type, help='The name of the app service plan',
                   completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                   configured_default='appserviceplan', id_part='name', local_context_attribute=None)

    with self.argument_context('webapp create') as c:
        c.argument('name', options_list=['--name', '-n'], help='name of the new web app',
                   validator=validate_site_create,
                   local_context_attribute=LocalContextAttribute(name='web_name', actions=[LocalContextAction.SET],
                                                                 scopes=['webapp', 'cupertino']))
        c.argument('startup_file', help="Linux only. The web's startup file")
        c.argument('docker_registry_server_user', options_list=['--docker-registry-server-user', '-s'], help='the container registry server username')
        c.argument('docker_registry_server_password', options_list=['--docker-registry-server-password', '-w'], help='The container registry server password. Required for private registries.')
        c.argument('multicontainer_config_type', options_list=['--multicontainer-config-type'], help="Linux only.", arg_type=get_enum_type(MULTI_CONTAINER_TYPES))
        c.argument('multicontainer_config_file', options_list=['--multicontainer-config-file'], help="Linux only. Config file for multicontainer apps. (local or remote)")
        c.argument('runtime', options_list=['--runtime', '-r'], help="canonicalized web runtime in the format of Framework:Version, e.g. \"PHP:7.2\". Allowed delimiters: \"|\" or \":\". If using powershell, please use the \":\" delimiter or be sure to properly escape the \"|\" character. "
                                                                     "Use `az webapp list-runtimes` for available list")  # TODO ADD completer
        c.argument('plan', options_list=['--plan', '-p'], configured_default='appserviceplan',
                   completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                   help="name or resource id of the app service plan. Use 'appservice plan create' to get one",
                   local_context_attribute=LocalContextAttribute(name='plan_name', actions=[LocalContextAction.GET]))
        c.argument('vnet', help="Name or resource ID of the regional virtual network. If there are multiple vnets of the same name across different resource groups, use vnet resource id to specify which vnet to use. If vnet name is used, by default, the vnet in the same resource group as the webapp will be used. Must be used with --subnet argument.")
        c.argument('subnet', help="Name or resource ID of the pre-existing subnet to have the webapp join. The --vnet is argument also needed if specifying subnet by name.")
        c.argument('https_only', help="Redirect all traffic made to an app using HTTP to HTTPS.",
                   arg_type=get_three_state_flag(return_label=True))
        c.ignore('language')
        c.ignore('using_webapp_up')

    with self.argument_context('webapp show') as c:
        c.argument('name', arg_type=webapp_name_arg_type)

    with self.argument_context('webapp list-instances') as c:
        c.argument('name', arg_type=webapp_name_arg_type, id_part=None)
        c.argument('slot', options_list=['--slot', '-s'], help='Name of the web app slot. Default to the productions slot if not specified.')

    with self.argument_context('webapp list-runtimes') as c:
        c.argument('linux', action='store_true', help='list runtime stacks for linux based web apps', deprecate_info=c.deprecate(redirect="--os-type"))
        c.argument('os_type', options_list=["--os", "--os-type"], help="limit the output to just windows or linux runtimes", arg_type=get_enum_type([LINUX_OS_NAME, WINDOWS_OS_NAME]))

    with self.argument_context('functionapp list-runtimes') as c:
        c.argument('os_type', options_list=["--os", "--os-type"], help="limit the output to just windows or linux runtimes", arg_type=get_enum_type([LINUX_OS_NAME, WINDOWS_OS_NAME]))

    with self.argument_context('webapp deleted list') as c:
        c.argument('name', arg_type=webapp_name_arg_type, id_part=None)
        c.argument('slot', options_list=['--slot', '-s'], help='Name of the deleted web app slot.')

    with self.argument_context('webapp deleted restore') as c:
        c.argument('deleted_id', options_list=['--deleted-id'], help='Resource ID of the deleted web app')
        c.argument('name', options_list=['--name', '-n'], help='name of the web app to restore the deleted content to')
        c.argument('slot', options_list=['--slot', '-s'], help='slot to restore the deleted content to')
        c.argument('restore_content_only', action='store_true',
                   help='restore only deleted files without web app settings')

    with self.argument_context('webapp traffic-routing') as c:
        c.argument('distribution', options_list=['--distribution', '-d'], nargs='+',
                   help='space-separated slot routings in a format of `<slot-name>=<percentage>` e.g. staging=50. Unused traffic percentage will go to the Production slot')

    with self.argument_context('webapp update') as c:
        c.argument('client_affinity_enabled', help="Enables sending session affinity cookies.",
                   arg_type=get_three_state_flag(return_label=True))
        c.argument('https_only', help="Redirect all traffic made to an app using HTTP to HTTPS.",
                   arg_type=get_three_state_flag(return_label=True))
        c.argument('force_dns_registration', help="If true, web app hostname is force registered with DNS",
                   arg_type=get_three_state_flag(return_label=True), deprecate_info=c.deprecate(expiration='3.0.0'))
        c.argument('skip_custom_domain_verification',
                   help="If true, custom (non *.azurewebsites.net) domains associated with web app are not verified",
                   arg_type=get_three_state_flag(return_label=True), deprecate_info=c.deprecate(expiration='3.0.0'))
        c.argument('ttl_in_seconds', help="Time to live in seconds for web app's default domain name",
                   arg_type=get_three_state_flag(return_label=True), deprecate_info=c.deprecate(expiration='3.0.0'))
        c.argument('skip_dns_registration', help="If true web app hostname is not registered with DNS on creation",
                   arg_type=get_three_state_flag(return_label=True), deprecate_info=c.deprecate(expiration='3.0.0'))
        c.argument('minimum_elastic_instance_count', options_list=["--minimum-elastic-instance-count", "-i"], type=int, is_preview=True, help="Minimum number of instances. App must be in an elastic scale App Service Plan.")
        c.argument('prewarmed_instance_count', options_list=["--prewarmed-instance-count", "-w"], type=int, is_preview=True, help="Number of preWarmed instances. App must be in an elastic scale App Service Plan.")

    with self.argument_context('webapp browse') as c:
        c.argument('logs', options_list=['--logs', '-l'], action='store_true',
                   help='Enable viewing the log stream immediately after launching the web app')
    with self.argument_context('webapp delete') as c:
        c.argument('name', arg_type=webapp_name_arg_type, local_context_attribute=None)
        c.argument('keep_empty_plan', action='store_true', help='keep empty app service plan')
        c.argument('keep_metrics', action='store_true', help='keep app metrics')
        c.argument('keep_dns_registration', action='store_true', help='keep DNS registration',
                   deprecate_info=c.deprecate(expiration='3.0.0'))

    with self.argument_context('webapp webjob') as c:
        c.argument('webjob_name', help='The name of the webjob', options_list=['--webjob-name', '-w'])
    with self.argument_context('webapp webjob continuous list') as c:
        c.argument('name', arg_type=webapp_name_arg_type, id_part=None)
    with self.argument_context('webapp webjob triggered list') as c:
        c.argument('name', arg_type=webapp_name_arg_type, id_part=None)

    for scope in ['webapp', 'functionapp', 'logicapp']:
        with self.argument_context(scope + ' create') as c:
            c.argument('deployment_container_image_name', options_list=['--deployment-container-image-name', '-i'],
                       help='Container image name from Docker Hub, e.g. publisher/image-name:tag')
            c.argument('deployment_local_git', action='store_true', options_list=['--deployment-local-git', '-l'],
                       help='enable local git')
            c.argument('deployment_zip', options_list=['--deployment-zip', '-z'],
                       help='perform deployment using zip file')
            c.argument('deployment_source_url', options_list=['--deployment-source-url', '-u'],
                       help='Git repository URL to link with manual integration')
            c.argument('deployment_source_branch', options_list=['--deployment-source-branch', '-b'],
                       help='the branch to deploy')
            c.argument('tags', arg_type=tags_type)

    for scope in ['webapp', 'functionapp']:
        with self.argument_context(scope) as c:
            c.argument('assign_identities', nargs='*', options_list=['--assign-identity'],
                       help='accept system or user assigned identities separated by spaces. Use \'[system]\' to refer system assigned identity, or a resource id to refer user assigned identity. Check out help for more examples')
            c.argument('scope', options_list=['--scope'], help="Scope that the system assigned identity can access")
            c.argument('role', options_list=['--role'], help="Role name or id the system assigned identity will have")

        with self.argument_context(scope + ' config ssl bind') as c:
            c.argument('ssl_type', help='The ssl cert type', arg_type=get_enum_type(['SNI', 'IP']))
        with self.argument_context(scope + ' config ssl upload') as c:
            c.argument('certificate_password', help='The ssl cert password')
            c.argument('certificate_file', type=file_type, help='The filepath for the .pfx file')
            c.argument('slot', options_list=['--slot', '-s'],
                       help='The name of the slot. Default to the productions slot if not specified')
        with self.argument_context(scope + ' config ssl') as c:
            c.argument('certificate_thumbprint', help='The ssl cert thumbprint')
        with self.argument_context(scope + ' config appsettings') as c:
            c.argument('settings', nargs='+', help="space-separated app settings in a format of `<name>=<value>`")
            c.argument('setting_names', nargs='+', help="space-separated app setting names")
        with self.argument_context(scope + ' config ssl import') as c:
            c.argument('key_vault', help='The name or resource ID of the Key Vault')
            c.argument('key_vault_certificate_name', help='The name of the certificate in Key Vault')
        with self.argument_context(scope + ' config ssl create') as c:
            c.argument('hostname', help='The custom domain name')
            c.argument('name', options_list=['--name', '-n'], help='Name of the web app.')
            c.argument('resource-group', options_list=['--resource-group', '-g'], help='Name of resource group.')
        with self.argument_context(scope + ' config ssl show') as c:
            c.argument('certificate_name', help='The name of the certificate')
        with self.argument_context(scope + ' config hostname') as c:
            c.argument('hostname', completer=get_hostname_completion_list,
                       help="hostname assigned to the site, such as custom domains", id_part='child_name_1')
        with self.argument_context(scope + ' deployment user') as c:
            c.argument('user_name', help='user name')
            c.argument('password', help='password, will prompt if not specified')
        with self.argument_context(scope + ' deployment source') as c:
            c.argument('manual_integration', action='store_true',
                       help='disable automatic sync between source control and web')
            c.argument('repo_url', options_list=['--repo-url', '-u'],
                       help='repository url to pull the latest source from, e.g. https://github.com/foo/foo-web')
            c.argument('branch', help='the branch name of the repository')
            c.argument('repository_type', help='repository type',
                       arg_type=get_enum_type(['git', 'mercurial', 'github', 'externalgit', 'localgit']))
            c.argument('git_token', help='Git access token required for auto sync')
            c.argument('github_action', options_list=['--github-action'], help='If using GitHub action, default to False')
        with self.argument_context(scope + ' identity') as c:
            c.argument('scope', help="The scope the managed identity has access to")
            c.argument('role', help="Role name or id the managed identity will be assigned")
        with self.argument_context(scope + ' identity assign') as c:
            c.argument('assign_identities', options_list=['--identities'], nargs='*', help="Space-separated identities to assign. Use '{0}' to refer to the system assigned identity. Default: '{0}'".format(MSI_LOCAL_ID))
        with self.argument_context(scope + ' identity remove') as c:
            c.argument('remove_identities', options_list=['--identities'], nargs='*', help="Space-separated identities to assign. Use '{0}' to refer to the system assigned identity. Default: '{0}'".format(MSI_LOCAL_ID))

        with self.argument_context(scope + ' deployment source config-zip') as c:
            c.argument('src', help='a zip file path for deployment')
            c.argument('build_remote', help='enable remote build during deployment',
                       arg_type=get_three_state_flag(return_label=True))
            c.argument('timeout', type=int, options_list=['--timeout', '-t'],
                       help='Configurable timeout in seconds for checking the status of deployment',
                       validator=validate_timeout_value)

        with self.argument_context(scope + ' config appsettings list') as c:
            c.argument('name', arg_type=(webapp_name_arg_type if scope == 'webapp' else functionapp_name_arg_type),
                       id_part=None)

        with self.argument_context(scope + ' config hostname list') as c:
            c.argument('webapp_name', arg_type=webapp_name_arg_type, id_part=None, options_list='--webapp-name')

        with self.argument_context(scope + ' cors') as c:
            c.argument('allowed_origins', options_list=['--allowed-origins', '-a'], nargs='*',
                       help='space separated origins that should be allowed to make cross-origin calls (for example: http://example.com:12345). To allow all, use "*" and remove all other origins from the list')

        with self.argument_context(scope + ' config set') as c:
            c.argument('number_of_workers', help='The number of workers to be allocated.', type=int)
            c.argument('remote_debugging_enabled', help='enable or disable remote debugging',
                       arg_type=get_three_state_flag(return_label=True))
            c.argument('web_sockets_enabled', help='enable or disable web sockets',
                       arg_type=get_three_state_flag(return_label=True))
            c.argument('always_on',
                       help='ensure web app gets loaded all the time, rather unloaded after been idle. Recommended when you have continuous web jobs running',
                       arg_type=get_three_state_flag(return_label=True))
            c.argument('auto_heal_enabled', help='enable or disable auto heal',
                       arg_type=get_three_state_flag(return_label=True))
            c.argument('use32_bit_worker_process', options_list=['--use-32bit-worker-process'],
                       help='use 32 bits worker process or not', arg_type=get_three_state_flag(return_label=True))
            c.argument('php_version', help='The version used to run your web app if using PHP, e.g., 5.5, 5.6, 7.0')
            c.argument('python_version', help='The version used to run your web app if using Python, e.g., 2.7, 3.4')
            c.argument('net_framework_version', help="The version used to run your web app if using .NET Framework, e.g., 'v4.0' for .NET 4.6 and 'v3.0' for .NET 3.5")
            c.argument('linux_fx_version', help="The runtime stack used for your linux-based webapp, e.g., \"RUBY|2.5.5\", \"NODE|12LTS\", \"PHP|7.2\", \"DOTNETCORE|2.1\". See https://aka.ms/linux-stacks for more info.")
            c.argument('windows_fx_version', help="A docker image name used for your windows container web app, e.g., microsoft/nanoserver:ltsc2016")
            if scope == 'functionapp':
                c.ignore('windows_fx_version')
            c.argument('pre_warmed_instance_count', options_list=['--prewarmed-instance-count'],
                       help="Number of pre-warmed instances a function app has")
            if scope == 'webapp':
                c.ignore('reserved_instance_count')
            c.argument('java_version',
                       help="The version used to run your web app if using Java, e.g., '1.7' for Java 7, '1.8' for Java 8")
            c.argument('java_container', help="The java container, e.g., Tomcat, Jetty")
            c.argument('java_container_version', help="The version of the java container, e.g., '8.0.23' for Tomcat")
            c.argument('min_tls_version',
                       help="The minimum version of TLS required for SSL requests, e.g., '1.0', '1.1', '1.2'")
            c.argument('http20_enabled', help="configures a web site to allow clients to connect over http2.0.",
                       arg_type=get_three_state_flag(return_label=True))
            c.argument('app_command_line', options_list=['--startup-file'],
                       help="The startup file for linux hosted web apps, e.g. 'process.json' for Node.js web")
            c.argument('ftps_state', help="Set the Ftps state value for an app. Default value is 'AllAllowed'.",
                       arg_type=get_enum_type(FTPS_STATE_TYPES))
            c.argument('vnet_route_all_enabled', help="Configure regional VNet integration to route all traffic to the VNet.",
                       arg_type=get_three_state_flag(return_label=True))
            c.argument('generic_configurations', nargs='+',
                       help='Provide site configuration list in a format of either `key=value` pair or `@<json_file>`. PowerShell and Windows Command Prompt users should use a JSON file to provide these configurations to avoid compatibility issues with escape characters.')

        with self.argument_context(scope + ' config container') as c:
            c.argument('docker_registry_server_url', options_list=['--docker-registry-server-url', '-r'],
                       help='the container registry server url')
            c.argument('docker_custom_image_name', options_list=['--docker-custom-image-name', '-c', '-i'],
                       help='the container custom image name and optionally the tag name (e.g., <registry-name>/<image-name>:<tag>)')
            c.argument('docker_registry_server_user', options_list=['--docker-registry-server-user', '-u'],
                       help='the container registry server username')
            c.argument('docker_registry_server_password', options_list=['--docker-registry-server-password', '-p'],
                       help='the container registry server password')
            c.argument('websites_enable_app_service_storage', options_list=['--enable-app-service-storage', '-t'],
                       help='enables platform storage (custom container only)',
                       arg_type=get_three_state_flag(return_label=True))
            c.argument('multicontainer_config_type', options_list=['--multicontainer-config-type'], help='config type',
                       arg_type=get_enum_type(MULTI_CONTAINER_TYPES))
            c.argument('multicontainer_config_file', options_list=['--multicontainer-config-file'],
                       help="config file for multicontainer apps")
            c.argument('show_multicontainer_config', action='store_true',
                       help='shows decoded config if a multicontainer config is set')

        with self.argument_context(scope + ' deployment container config') as c:
            c.argument('enable', options_list=['--enable-cd', '-e'], help='enable/disable continuous deployment',
                       arg_type=get_three_state_flag(return_label=True))

    with self.argument_context('webapp config connection-string list') as c:
        c.argument('name', arg_type=webapp_name_arg_type, id_part=None)

    with self.argument_context('webapp config storage-account list') as c:
        c.argument('name', arg_type=webapp_name_arg_type, id_part=None)

    with self.argument_context('webapp config hostname') as c:
        c.argument('webapp_name',
                   help="webapp name. You can configure the default using `az configure --defaults web=<name>`",
                   configured_default='web',
                   completer=get_resource_name_completion_list('Microsoft.Web/sites'), id_part='name',
                   local_context_attribute=LocalContextAttribute(name='web_name', actions=[LocalContextAction.GET]))
    with self.argument_context('webapp deployment list-publishing-profiles') as c:
        c.argument('xml', options_list=['--xml'], required=False, help='retrieves the publishing profile details in XML format')
    with self.argument_context('webapp deployment slot') as c:
        c.argument('slot', help='the name of the slot')
        c.argument('webapp', arg_type=name_arg_type, completer=get_resource_name_completion_list('Microsoft.Web/sites'),
                   help='Name of the webapp', id_part='name',
                   local_context_attribute=LocalContextAttribute(name='web_name', actions=[LocalContextAction.GET]))
        c.argument('auto_swap_slot', help='target slot to auto swap', default='production')
        c.argument('disable', help='disable auto swap', action='store_true')
        c.argument('target_slot', help="target slot to swap, default to 'production'")
        c.argument('preserve_vnet', help="preserve Virtual Network to the slot during swap, default to 'true'",
                   arg_type=get_three_state_flag(return_label=True))
    with self.argument_context('webapp deployment slot create') as c:
        c.argument('configuration_source',
                   help="source slot to clone configurations from. Use web app's name to refer to the production slot")
        c.argument('deployment_container_image_name', options_list=['--deployment-container-image-name', '-i'],
                   help='Container image name, e.g. publisher/image-name:tag')
        c.argument('docker_registry_server_password', options_list=['--docker-registry-server-password', '-w'],
                   help='The container registry server password')
        c.argument('docker_registry_server_user', options_list=['--docker-registry-server-user', '-u'], help='the container registry server username')
    with self.argument_context('webapp deployment slot swap') as c:
        c.argument('action',
                   help="swap types. use 'preview' to apply target slot's settings on the source slot first; use 'swap' to complete it; use 'reset' to reset the swap",
                   arg_type=get_enum_type(['swap', 'preview', 'reset']))

    with self.argument_context('webapp deployment github-actions')as c:
        c.argument('name', arg_type=webapp_name_arg_type)
        c.argument('resource_group', arg_type=resource_group_name_type, options_list=['--resource-group', '-g'])
        c.argument('repo', help='The GitHub repository to which the workflow file will be added. In the format: <owner>/<repository-name>')
        c.argument('token', help='A Personal Access Token with write access to the specified repository. For more information: https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line')
        c.argument('slot', options_list=['--slot', '-s'], help='The name of the slot. Default to the production slot if not specified.')
        c.argument('branch', options_list=['--branch', '-b'], help='The branch to which the workflow file will be added. Defaults to "master" if not specified.')
        c.argument('login_with_github', help='Interactively log in with GitHub to retrieve the Personal Access Token', action='store_true')

    with self.argument_context('webapp deployment github-actions add')as c:
        c.argument('runtime', options_list=['--runtime', '-r'], help='Canonicalized web runtime in the format of Framework|Version, e.g. "PHP|5.6". Use "az webapp list-runtimes" for available list.')
        c.argument('force', options_list=['--force', '-f'], help='When true, the command will overwrite any workflow file with a conflicting name.', action='store_true')

    with self.argument_context('webapp log config') as c:
        c.argument('application_logging', help='configure application logging',
                   arg_type=get_enum_type(['filesystem', 'azureblobstorage', 'off']))
        c.argument('detailed_error_messages', help='configure detailed error messages',
                   arg_type=get_three_state_flag(return_label=True))
        c.argument('failed_request_tracing', help='configure failed request tracing',
                   arg_type=get_three_state_flag(return_label=True))
        c.argument('level', help='logging level',
                   arg_type=get_enum_type(['error', 'warning', 'information', 'verbose']))
        c.argument('web_server_logging', help='configure Web server logging',
                   arg_type=get_enum_type(['off', 'filesystem']))
        c.argument('docker_container_logging', help='configure gathering STDOUT and STDERR output from container',
                   arg_type=get_enum_type(['off', 'filesystem']))

    with self.argument_context('webapp log tail') as c:
        c.argument('provider',
                   help="By default all live traces configured by `az webapp log config` will be shown, but you can scope to certain providers/folders, e.g. 'application', 'http', etc. For details, check out https://github.com/projectkudu/kudu/wiki/Diagnostic-Log-Stream")

    with self.argument_context('webapp log download') as c:
        c.argument('log_file', default='webapp_logs.zip', type=file_type, completer=FilesCompleter(),
                   help='the downloaded zipped log file path')

    with self.argument_context('webapp log deployment show') as c:
        c.argument('name', arg_type=webapp_name_arg_type, id_part=None)
        c.argument('resource_group', arg_type=resource_group_name_type)
        c.argument('slot', options_list=['--slot', '-s'], help="the name of the slot. Default to the productions slot if not specified")
        c.argument('deployment_id', options_list=['--deployment-id'], help='Deployment ID. If none specified, returns the deployment logs of the latest deployment.')

    with self.argument_context('webapp log deployment list') as c:
        c.argument('name', arg_type=webapp_name_arg_type, id_part=None)
        c.argument('resource_group', arg_type=resource_group_name_type)
        c.argument('slot', options_list=['--slot', '-s'], help="the name of the slot. Default to the productions slot if not specified")

    with self.argument_context('functionapp log deployment show') as c:
        c.argument('name', arg_type=functionapp_name_arg_type, id_part=None)
        c.argument('resource_group', arg_type=resource_group_name_type)
        c.argument('slot', options_list=['--slot', '-s'], help="the name of the slot. Default to the productions slot if not specified")
        c.argument('deployment_id', options_list=['--deployment-id'], help='Deployment ID. If none specified, returns the deployment logs of the latest deployment.')

    with self.argument_context('functionapp log deployment list') as c:
        c.argument('name', arg_type=functionapp_name_arg_type, id_part=None)
        c.argument('resource_group', arg_type=resource_group_name_type)
        c.argument('slot', options_list=['--slot', '-s'], help="the name of the slot. Default to the productions slot if not specified")

    for scope in ['appsettings', 'connection-string']:
        with self.argument_context('webapp config ' + scope) as c:
            c.argument('settings', nargs='+', help="space-separated {} in a format of `<name>=<value>`".format(scope))
            c.argument('slot_settings', nargs='+',
                       help="space-separated slot {} in a format of either `<name>=<value>` or `@<json_file>`".format(
                           scope))
            c.argument('setting_names', nargs='+', help="space-separated {} names".format(scope))

    with self.argument_context('webapp config connection-string') as c:
        c.argument('connection_string_type', options_list=['--connection-string-type', '-t'],
                   help='connection string type', arg_type=get_enum_type(ConnectionStringType))
        c.argument('ids', options_list=['--ids'],
                   help="One or more resource IDs (space delimited). If provided no other 'Resource Id' arguments should be specified.",
                   required=True)
        c.argument('resource_group', options_list=['--resource-group', '-g'],
                   help='Name of resource group. You can configure the default group using `az configure --default-group=<name>`. If `--ids` is provided this should NOT be specified.')
        c.argument('name', options_list=['--name', '-n'],
                   help='Name of the web app. You can configure the default using `az configure --defaults web=<name>`. If `--ids` is provided this should NOT be specified.',
                   local_context_attribute=LocalContextAttribute(name='web_name', actions=[LocalContextAction.GET]))

    with self.argument_context('webapp config storage-account') as c:
        c.argument('custom_id', options_list=['--custom-id', '-i'], help='name of the share configured within the web app')
        c.argument('storage_type', options_list=['--storage-type', '-t'], help='storage type',
                   arg_type=get_enum_type(AzureStorageType))
        c.argument('account_name', options_list=['--account-name', '-a'], help='storage account name')
        c.argument('share_name', options_list=['--share-name', '--sn'],
                   help='name of the file share as given in the storage account')
        c.argument('access_key', options_list=['--access-key', '-k'], help='storage account access key')
        c.argument('mount_path', options_list=['--mount-path', '-m'],
                   help='the path which the web app uses to read-write data ex: /share1 or /share2')
        c.argument('slot', options_list=['--slot', '-s'],
                   help="the name of the slot. Default to the productions slot if not specified")
    with self.argument_context('webapp config storage-account add') as c:
        c.argument('slot_setting', options_list=['--slot-setting'], help="slot setting")
    with self.argument_context('webapp config storage-account update') as c:
        c.argument('slot_setting', options_list=['--slot-setting'], help="slot setting")

    with self.argument_context('webapp config backup') as c:
        c.argument('storage_account_url', help='URL with SAS token to the blob storage container',
                   options_list=['--container-url'])
        c.argument('webapp_name', help='The name of the web app',
                   local_context_attribute=LocalContextAttribute(name='web_name', actions=[LocalContextAction.GET]))
        c.argument('db_name', help='Name of the database in the backup', arg_group='Database')
        c.argument('db_connection_string', help='Connection string for the database in the backup',
                   arg_group='Database')
        c.argument('db_type', help='Type of database in the backup', arg_group='Database',
                   arg_type=get_enum_type(DatabaseType))

    with self.argument_context('webapp config backup create') as c:
        c.argument('backup_name',
                   help='Name of the backup. If unspecified, the backup will be named with the web app name and a timestamp',
                   local_context_attribute=LocalContextAttribute(name='backup_name', actions=[LocalContextAction.SET],
                                                                 scopes=['webapp']))

    with self.argument_context('webapp config backup update') as c:
        c.argument('backup_name',
                   help='Name of the backup. If unspecified, the backup will be named with the web app name and a timestamp',
                   local_context_attribute=LocalContextAttribute(name='backup_name', actions=[LocalContextAction.GET]))
        c.argument('frequency',
                   help='How often to backup. Use a number followed by d or h, e.g. 5d = 5 days, 2h = 2 hours')
        c.argument('keep_at_least_one_backup', help='Always keep one backup, regardless of how old it is',
                   options_list=['--retain-one'], arg_type=get_three_state_flag(return_label=True))
        c.argument('retention_period_in_days',
                   help='How many days to keep a backup before automatically deleting it. Set to 0 for indefinite retention',
                   options_list=['--retention'])

    with self.argument_context('webapp config backup restore') as c:
        c.argument('backup_name', help='Name of the backup to restore',
                   local_context_attribute=LocalContextAttribute(name='backup_name', actions=[LocalContextAction.GET]))
        c.argument('target_name',
                   help='The name to use for the restored web app. If unspecified, will default to the name that was used when the backup was created')
        c.argument('overwrite', help='Overwrite the source web app, if --target-name is not specified',
                   action='store_true')
        c.argument('ignore_hostname_conflict', help='Ignores custom hostnames stored in the backup',
                   action='store_true')

    with self.argument_context('webapp config snapshot') as c:
        c.argument('name', arg_type=webapp_name_arg_type)
        c.argument('slot', options_list=['--slot', '-s'], help='The name of the slot.')

    with self.argument_context('webapp config snapshot list') as c:
        c.argument('name', arg_type=webapp_name_arg_type, id_part=None)

    with self.argument_context('webapp config snapshot restore') as c:
        c.argument('time', help='Timestamp of the snapshot to restore.')
        c.argument('restore_content_only', help='Restore the web app files without restoring the settings.')
        c.argument('source_resource_group', help='Name of the resource group to retrieve snapshot from.')
        c.argument('source_name', help='Name of the web app to retrieve snapshot from.')
        c.argument('source_slot', help='Name of the web app slot to retrieve snapshot from.')

    with self.argument_context('webapp auth update') as c:
        c.argument('enabled', arg_type=get_three_state_flag(return_label=True))
        c.argument('token_store_enabled', options_list=['--token-store'],
                   arg_type=get_three_state_flag(return_label=True), help='use App Service Token Store')
        c.argument('action', arg_type=get_enum_type(AUTH_TYPES))
        c.argument('runtime_version',
                   help='Runtime version of the Authentication/Authorization feature in use for the current app')
        c.argument('token_refresh_extension_hours', type=float, help="Hours, must be formattable into a float")
        c.argument('allowed_external_redirect_urls', nargs='+', help="One or more urls (space-delimited).")
        c.argument('client_id', options_list=['--aad-client-id'], arg_group='Azure Active Directory',
                   help='Application ID to integrate AAD organization account Sign-in into your web app')
        c.argument('client_secret', options_list=['--aad-client-secret'], arg_group='Azure Active Directory',
                   help='AAD application secret')
        c.argument('client_secret_certificate_thumbprint', options_list=['--aad-client-secret-certificate-thumbprint', '--thumbprint'], arg_group='Azure Active Directory',
                   help='Alternative to AAD Client Secret, thumbprint of a certificate used for signing purposes')
        c.argument('allowed_audiences', nargs='+', options_list=['--aad-allowed-token-audiences'],
                   arg_group='Azure Active Directory', help="One or more token audiences (comma-delimited).")
        c.argument('issuer', options_list=['--aad-token-issuer-url'],
                   help='This url can be found in the JSON output returned from your active directory endpoint using your tenantID. The endpoint can be queried from `az cloud show` at \"endpoints.activeDirectory\". '
                        'The tenantID can be found using `az account show`. Get the \"issuer\" from the JSON at <active directory endpoint>/<tenantId>/.well-known/openid-configuration.',
                   arg_group='Azure Active Directory')
        c.argument('facebook_app_id', arg_group='Facebook',
                   help="Application ID to integrate Facebook Sign-in into your web app")
        c.argument('facebook_app_secret', arg_group='Facebook', help='Facebook Application client secret')
        c.argument('facebook_oauth_scopes', nargs='+',
                   help="One or more facebook authentication scopes (comma-delimited).", arg_group='Facebook')
        c.argument('twitter_consumer_key', arg_group='Twitter',
                   help='Application ID to integrate Twitter Sign-in into your web app')
        c.argument('twitter_consumer_secret', arg_group='Twitter', help='Twitter Application client secret')
        c.argument('google_client_id', arg_group='Google',
                   help='Application ID to integrate Google Sign-in into your web app')
        c.argument('google_client_secret', arg_group='Google', help='Google Application client secret')
        c.argument('google_oauth_scopes', nargs='+', help="One or more Google authentication scopes (space-delimited).",
                   arg_group='Google')
        c.argument('microsoft_account_client_id', arg_group='Microsoft',
                   help="AAD V2 Application ID to integrate Microsoft account Sign-in into your web app")
        c.argument('microsoft_account_client_secret', arg_group='Microsoft', help='AAD V2 Application client secret')
        c.argument('microsoft_account_oauth_scopes', nargs='+',
                   help="One or more Microsoft authentification scopes (comma-delimited).", arg_group='Microsoft')

    with self.argument_context('webapp hybrid-connection') as c:
        c.argument('name', arg_type=webapp_name_arg_type, id_part=None)
        c.argument('slot', help="the name of the slot. Default to the productions slot if not specified")
        c.argument('namespace', help="Hybrid connection namespace")
        c.argument('hybrid_connection', help="Hybrid connection name")

    with self.argument_context('functionapp hybrid-connection') as c:
        c.argument('name', id_part=None, local_context_attribute=LocalContextAttribute(name='functionapp_name',
                                                                                       actions=[
                                                                                           LocalContextAction.GET]))
        c.argument('slot', help="the name of the slot. Default to the productions slot if not specified")
        c.argument('namespace', help="Hybrid connection namespace")
        c.argument('hybrid_connection', help="Hybrid connection name")

    with self.argument_context('appservice hybrid-connection set-key') as c:
        c.argument('plan', help="AppService plan",
                   local_context_attribute=LocalContextAttribute(name='plan_name', actions=[LocalContextAction.GET]))
        c.argument('namespace', help="Hybrid connection namespace")
        c.argument('hybrid_connection', help="Hybrid connection name")
        c.argument('key_type', help="Which key (primary or secondary) should be used")

    with self.argument_context('appservice vnet-integration list') as c:
        c.argument('plan', help="AppService plan",
                   local_context_attribute=LocalContextAttribute(name='plan_name', actions=[LocalContextAction.GET]))
        c.argument('resource_group', arg_type=resource_group_name_type)

    with self.argument_context('webapp up') as c:
        c.argument('name', arg_type=webapp_name_arg_type,
                   local_context_attribute=LocalContextAttribute(name='web_name', actions=[LocalContextAction.GET,
                                                                                           LocalContextAction.SET],
                                                                 scopes=['webapp', 'cupertino']))
        c.argument('plan', options_list=['--plan', '-p'],
                   completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                   help="name of the app service plan associated with the webapp",
                   configured_default='appserviceplan')
        c.argument('sku', arg_type=sku_arg_type)
        c.argument('os_type', options_list=['--os-type'], arg_type=get_enum_type(OS_TYPES), help="Set the OS type for the app to be created.")
        c.argument('runtime', options_list=['--runtime', '-r'], help="canonicalized web runtime in the format of Framework:Version, e.g. \"PHP:7.2\". Allowed delimiters: \"|\" or \":\". If using powershell, please use the \":\" delimiter or be sure to properly escape the \"|\" character. "
                                                                     "Use `az webapp list-runtimes` for available list.")
        c.argument('dryrun', help="show summary of the create and deploy operation instead of executing it",
                   default=False, action='store_true')
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('launch_browser', help="Launch the created app using the default browser", default=False,
                   action='store_true', options_list=['--launch-browser', '-b'])
        c.argument('logs',
                   help="Configure default logging required to enable viewing log stream immediately after launching the webapp",
                   default=False, action='store_true')
        c.argument('html', help="Ignore app detection and deploy as an html app", default=False, action='store_true')
        c.argument('app_service_environment', options_list=['--app-service-environment', '-e'], help='name or resource ID of the (pre-existing) App Service Environment to deploy to. Requires an Isolated V2 sku [I1v2, I2v2, I3v2]')

    with self.argument_context('webapp ssh') as c:
        c.argument('port', options_list=['--port', '-p'],
                   help='Port for the remote connection. Default: Random available port', type=int)
        c.argument('timeout', options_list=['--timeout', '-t'], help='timeout in seconds. Defaults to none', type=int)
        c.argument('instance', options_list=['--instance', '-i'], help='Webapp instance to connect to. Defaults to none.')

    with self.argument_context('webapp create-remote-connection') as c:
        c.argument('port', options_list=['--port', '-p'],
                   help='Port for the remote connection. Default: Random available port', type=int)
        c.argument('timeout', options_list=['--timeout', '-t'], help='timeout in seconds. Defaults to none', type=int)
        c.argument('instance', options_list=['--instance', '-i'], help='Webapp instance to connect to. Defaults to none.')

    with self.argument_context('webapp vnet-integration') as c:
        c.argument('name', arg_type=webapp_name_arg_type, id_part=None)
        c.argument('slot', help="The name of the slot. Default to the productions slot if not specified.")
        c.argument('vnet', help="The name or resource ID of the Vnet",
                   local_context_attribute=LocalContextAttribute(name='vnet_name', actions=[LocalContextAction.GET]))
        c.argument('subnet', help="The name or resource ID of the subnet",
                   local_context_attribute=LocalContextAttribute(name='subnet_name', actions=[LocalContextAction.GET]))
        c.argument('skip_delegation_check', help="Skip check if you do not have permission or the VNet is in another subscription.",
                   arg_type=get_three_state_flag(return_label=True))

    with self.argument_context('webapp deploy') as c:
        c.argument('name', options_list=['--name', '-n'], help='Name of the webapp to deploy to.')
        c.argument('src_path', options_list=['--src-path'], help='Path of the artifact to be deployed. Ex: "myapp.zip" or "/myworkspace/apps/myapp.war"')
        c.argument('src_url', options_list=['--src-url'], help='URL of the artifact. The webapp will pull the artifact from this URL. Ex: "http://mysite.com/files/myapp.war?key=123"')
        c.argument('target_path', options_list=['--target-path'], help='Absolute path that the artifact should be deployed to. Defaults to "home/site/wwwroot/" Ex: "/home/site/deployments/tools/", "/home/site/scripts/startup-script.sh".')
        c.argument('artifact_type', options_list=['--type'], help='Used to override the type of artifact being deployed.', choices=['war', 'jar', 'ear', 'lib', 'startup', 'static', 'zip'])
        c.argument('is_async', options_list=['--async'], help='If true, the artifact is deployed asynchronously. (The command will exit once the artifact is pushed to the web app.)', choices=['true', 'false'])
        c.argument('restart', options_list=['--restart'], help='If true, the web app will be restarted following the deployment. Set this to false if you are deploying multiple artifacts and do not want to restart the site on the earlier deployments.', choices=['true', 'false'])
        c.argument('clean', options_list=['--clean'], help='If true, cleans the target directory prior to deploying the file(s). Default value is determined based on artifact type.', choices=['true', 'false'])
        c.argument('ignore_stack', options_list=['--ignore-stack'], help='If true, any stack-specific defaults are ignored.', choices=['true', 'false'])
        c.argument('timeout', options_list=['--timeout'], help='Timeout for the deployment operation in milliseconds.')
        c.argument('slot', help="The name of the slot. Default to the productions slot if not specified.")

    with self.argument_context('functionapp deploy') as c:
        c.argument('name', options_list=['--name', '-n'], help='Name of the function app to deploy to.')
        c.argument('src_path', options_list=['--src-path'], help='Path of the artifact to be deployed. Ex: "myapp.zip" or "/myworkspace/apps/myapp.war"')
        c.argument('src_url', options_list=['--src-url'], help='URL of the artifact. The webapp will pull the artifact from this URL. Ex: "http://mysite.com/files/myapp.war?key=123"')
        c.argument('target_path', options_list=['--target-path'], help='Absolute path that the artifact should be deployed to. Defaults to "home/site/wwwroot/". Ex: "/home/site/deployments/tools/", "/home/site/scripts/startup-script.sh".')
        c.argument('artifact_type', options_list=['--type'], help='Used to override the type of artifact being deployed.', choices=['war', 'jar', 'ear', 'lib', 'startup', 'static', 'zip'])
        c.argument('is_async', options_list=['--async'], help='Asynchronous deployment', choices=['true', 'false'])
        c.argument('restart', options_list=['--restart'], help='If true, the web app will be restarted following the deployment, default value is true. Set this to false if you are deploying multiple artifacts and do not want to restart the site on the earlier deployments.', choices=['true', 'false'])
        c.argument('clean', options_list=['--clean'], help='If true, cleans the target directory prior to deploying the file(s). Default value is determined based on artifact type.', choices=['true', 'false'])
        c.argument('ignore_stack', options_list=['--ignore-stack'], help='If true, any stack-specific defaults are ignored.', choices=['true', 'false'])
        c.argument('timeout', options_list=['--timeout'], help='Timeout for the deployment operation in milliseconds.')
        c.argument('slot', help="The name of the slot. Default to the productions slot if not specified.")

    with self.argument_context('functionapp create') as c:
        c.argument('vnet', options_list=['--vnet'], help="Name or resource ID of the regional virtual network. If there are multiple vnets of the same name across different resource groups, use vnet resource id to specify which vnet to use. If vnet name is used, by default, the vnet in the same resource group as the webapp will be used. Must be used with --subnet argument.")
        c.argument('subnet', options_list=['--subnet'], help="Name or resource ID of the pre-existing subnet to have the webapp join. The --vnet is argument also needed if specifying subnet by name.")

    with self.argument_context('functionapp vnet-integration') as c:
        c.argument('name', arg_type=functionapp_name_arg_type, id_part=None)
        c.argument('slot', help="The name of the slot. Default to the productions slot if not specified")
        c.argument('vnet', help="The name or resource ID of the Vnet",
                   local_context_attribute=LocalContextAttribute(name='vnet_name', actions=[LocalContextAction.GET]))
        c.argument('subnet', help="The name or resource ID of the subnet",
                   local_context_attribute=LocalContextAttribute(name='subnet_name', actions=[LocalContextAction.GET]))
        c.argument('skip_delegation_check', help="Skip check if you do not have permission or the VNet is in another subscription.",
                   arg_type=get_three_state_flag(return_label=True))

    for scope in ['functionapp', 'logicapp']:
        app_type = scope[:-3]  # 'function' or 'logic'
        with self.argument_context(scope) as c:
            c.ignore('app_instance')
            c.argument('name', arg_type=name_arg_type_dict[scope], id_part='name', help='name of the {} app'.format(app_type))
            c.argument('slot', options_list=['--slot', '-s'],
                       help="the name of the slot. Default to the productions slot if not specified")

        with self.argument_context(scope + ' create') as c:
            c.argument('plan', options_list=['--plan', '-p'], configured_default='appserviceplan',
                       completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                       help="name or resource id of the {} app service plan. Use 'appservice plan create' to get one. If using an App Service plan from a different resource group, the full resource id must be used and not the plan name.".format(scope),
                       local_context_attribute=LocalContextAttribute(name='plan_name', actions=[LocalContextAction.GET]))
            c.argument('name', options_list=['--name', '-n'], help='name of the new {} app'.format(app_type),
                       local_context_attribute=LocalContextAttribute(name=scope + '_name', actions=[LocalContextAction.SET], scopes=[scope]))
            c.argument('storage_account', options_list=['--storage-account', '-s'],
                       help='Provide a string value of a Storage Account in the provided Resource Group. Or Resource ID of a Storage Account in a different Resource Group',
                       local_context_attribute=LocalContextAttribute(name='storage_account_name', actions=[LocalContextAction.GET]))
            c.argument('consumption_plan_location', options_list=['--consumption-plan-location', '-c'],
                       help="Geographic location where {} app will be hosted. Use `az {} list-consumption-locations` to view available locations.".format(app_type, scope))
            c.argument('os_type', arg_type=get_enum_type(OS_TYPES), help="Set the OS type for the app to be created.")
            c.argument('app_insights_key', help="Instrumentation key of App Insights to be added.")
            c.argument('app_insights',
                       help="Name of the existing App Insights project to be added to the {} app. Must be in the ".format(app_type) +
                       "same resource group.")
            c.argument('disable_app_insights', arg_type=get_three_state_flag(return_label=True),
                       help="Disable creating application insights resource during {} create. No logs will be available.".format(scope))
            c.argument('docker_registry_server_user', options_list=['--docker-registry-server-user', '-d'], help='The container registry server username.')
            c.argument('docker_registry_server_password', options_list=['--docker-registry-server-password', '-w'],
                       help='The container registry server password. Required for private registries.')
            if scope == 'functionapp':
                c.argument('functions_version', help='The functions app version. NOTE: This will be required starting the next release cycle', arg_type=get_enum_type(FUNCTIONS_VERSIONS))
                c.argument('runtime', help='The functions runtime stack. Use "az functionapp list-runtimes" to check supported runtimes and versions')
                c.argument('runtime_version',
                           help='The version of the functions runtime stack. '
                           'The functions runtime stack. Use "az functionapp list-runtimes" to check supported runtimes and versions')

    with self.argument_context('functionapp config hostname') as c:
        c.argument('webapp_name', arg_type=functionapp_name_arg_type, id_part='name')
    # For commands with shared impl between web app and function app and has output, we apply type validation to avoid confusions
    with self.argument_context('functionapp show') as c:
        c.argument('name', arg_type=functionapp_name_arg_type)
    with self.argument_context('functionapp delete') as c:
        c.argument('name', arg_type=functionapp_name_arg_type, local_context_attribute=None)
    with self.argument_context('functionapp config appsettings') as c:
        c.argument('slot_settings', nargs='+', help="space-separated slot app settings in a format of `<name>=<value>`")

    with self.argument_context('logicapp show') as c:
        c.argument('name', arg_type=logicapp_name_arg_type)
    with self.argument_context('logicapp delete') as c:
        c.argument('name', arg_type=logicapp_name_arg_type, local_context_attribute=None)

    with self.argument_context('functionapp plan') as c:
        c.argument('name', arg_type=name_arg_type, help='The name of the app service plan',
                   completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                   configured_default='appserviceplan', id_part='name',
                   local_context_attribute=LocalContextAttribute(name='plan_name', actions=[LocalContextAction.GET]))
        c.argument('is_linux', arg_type=get_three_state_flag(return_label=True), required=False,
                   help='host function app on Linux worker')
        c.argument('number_of_workers', options_list=['--number-of-workers', '--min-instances'],
                   help='The number of workers for the app service plan.')
        c.argument('max_burst',
                   help='The maximum number of elastic workers for the plan.')
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('functionapp update') as c:
        c.argument('plan', required=False, help='The name or resource id of the plan to update the functionapp with.')
        c.argument('force', required=False, help='Required if attempting to migrate functionapp from Premium to Consumption --plan.',
                   action='store_true')

    with self.argument_context('functionapp plan create') as c:
        c.argument('name', arg_type=name_arg_type, help='The name of the app service plan',
                   completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                   configured_default='appserviceplan', id_part='name',
                   local_context_attribute=LocalContextAttribute(name='plan_name', actions=[LocalContextAction.SET],
                                                                 scopes=['appservice', 'webapp', 'functionapp']))
        c.argument('zone_redundant', options_list=['--zone-redundant', '-z'], help='Enable zone redundancy for high availability. Cannot be changed after plan creation. Minimum instance count is 3.')
        c.argument('sku', required=True, help='The SKU of the app service plan. e.g., F1(Free), D1(Shared), B1(Basic Small), '
                                              'B2(Basic Medium), B3(Basic Large), S1(Standard Small), '
                                              'P1V2(Premium V2 Small), I1 (Isolated Small), I2 (Isolated Medium), I3 (Isolated Large), K1 '
                                              '(Kubernetes).')

    with self.argument_context('functionapp plan update') as c:
        c.argument('sku', required=False, help='The SKU of the app service plan.')

    with self.argument_context('functionapp plan delete') as c:
        c.argument('name', arg_type=name_arg_type, help='The name of the app service plan',
                   completer=get_resource_name_completion_list('Microsoft.Web/serverFarms'),
                   configured_default='appserviceplan', id_part='name',
                   local_context_attribute=None)

    with self.argument_context('functionapp deployment list-publishing-profiles') as c:
        c.argument('xml', options_list=['--xml'], required=False, help='retrieves the publishing profile details in XML format')
    with self.argument_context('functionapp deployment slot') as c:
        c.argument('slot', help='the name of the slot')
        # This is set to webapp to simply reuse webapp functions, without rewriting same functions for function apps.
        # The help will still show "-n or --name", so it should not be a problem to do it this way
        c.argument('webapp', arg_type=functionapp_name_arg_type,
                   completer=get_resource_name_completion_list('Microsoft.Web/sites'),
                   help='Name of the function app', id_part='name')
        c.argument('auto_swap_slot', help='target slot to auto swap', default='production')
        c.argument('disable', help='disable auto swap', action='store_true')
        c.argument('target_slot', help="target slot to swap, default to 'production'")
        c.argument('preserve_vnet', help="preserve Virtual Network to the slot during swap, default to 'true'",
                   arg_type=get_three_state_flag(return_label=True))
    with self.argument_context('functionapp deployment slot create') as c:
        c.argument('configuration_source',
                   help="source slot to clone configurations from. Use function app's name to refer to the production slot")
        c.argument('deployment_container_image_name', options_list=['--deployment-container-image-name', '-i'],
                   help='Container image name, e.g. publisher/image-name:tag')
        c.argument('docker_registry_server_password', options_list=['--docker-registry-server-password', '-d'],
                   help='The container registry server password')
        c.argument('docker_registry_server_user', options_list=['--docker-registry-server-user', '-u'], help='the container registry server username')
    with self.argument_context('functionapp deployment slot swap') as c:
        c.argument('action',
                   help="swap types. use 'preview' to apply target slot's settings on the source slot first; use 'swap' to complete it; use 'reset' to reset the swap",
                   arg_type=get_enum_type(['swap', 'preview', 'reset']))

    with self.argument_context('functionapp keys', id_part=None) as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type,)
        c.argument('name', arg_type=functionapp_name_arg_type,
                   completer=get_resource_name_completion_list('Microsoft.Web/sites'),
                   help='Name of the function app')
        c.argument('slot', options_list=['--slot', '-s'],
                   help="The name of the slot. Defaults to the productions slot if not specified")
    with self.argument_context('functionapp keys set', id_part=None) as c:
        c.argument('key_name', help="Name of the key to set.")
        c.argument('key_value', help="Value of the new key. If not provided, a value will be generated.")
        c.argument('key_type', help="Type of key.", arg_type=get_enum_type(['systemKey', 'functionKeys', 'masterKey']))
    with self.argument_context('functionapp keys delete', id_part=None) as c:
        c.argument('key_name', help="Name of the key to set.")
        c.argument('key_type', help="Type of key.", arg_type=get_enum_type(['systemKey', 'functionKeys', 'masterKey']))

    with self.argument_context('functionapp function', id_part=None) as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type,)
        c.argument('name', arg_type=functionapp_name_arg_type,
                   completer=get_resource_name_completion_list('Microsoft.Web/sites'),
                   help='Name of the function app')
        c.argument('function_name', help="Name of the Function")
    with self.argument_context('functionapp function keys', id_part=None) as c:
        c.argument('slot', options_list=['--slot', '-s'],
                   help="The name of the slot. Defaults to the productions slot if not specified")
    with self.argument_context('functionapp function keys set', id_part=None) as c:
        c.argument('key_name', help="Name of the key to set.")
        c.argument('key_value', help="Value of the new key. If not provided, a value will be generated.")
    with self.argument_context('functionapp function keys delete', id_part=None) as c:
        c.argument('key_name', help="Name of the key to set.")

    # Access Restriction Commands
    for scope in ['webapp', 'functionapp']:
        with self.argument_context(scope + ' config access-restriction show') as c:
            c.argument('name', arg_type=(webapp_name_arg_type if scope == 'webapp' else functionapp_name_arg_type))

        with self.argument_context(scope + ' config access-restriction add') as c:
            c.argument('name', arg_type=(webapp_name_arg_type if scope == 'webapp' else functionapp_name_arg_type))
            c.argument('rule_name', options_list=['--rule-name', '-r'],
                       help='Name of the access restriction rule to add')
            c.argument('priority', options_list=['--priority', '-p'],
                       help="Priority of the access restriction rule")
            c.argument('description', help='Description of the access restriction rule')
            c.argument('action', arg_type=get_enum_type(ACCESS_RESTRICTION_ACTION_TYPES),
                       help="Allow or deny access")
            c.argument('ip_address', help="IP address or CIDR range (optional comma separated list of up to 8 ranges)",
                       validator=validate_ip_address)
            c.argument('service_tag', help="Service Tag (optional comma separated list of up to 8 tags)",
                       validator=validate_service_tag)
            c.argument('vnet_name', help="vNet name")
            c.argument('subnet', help="Subnet name (requires vNet name) or subnet resource id")
            c.argument('ignore_missing_vnet_service_endpoint',
                       options_list=['--ignore-missing-endpoint', '-i'],
                       help='Create access restriction rule with checking if the subnet has Microsoft.Web service endpoint enabled',
                       arg_type=get_three_state_flag(), default=False)
            c.argument('scm_site', help='True if access restrictions is added for scm site',
                       arg_type=get_three_state_flag())
            c.argument('vnet_resource_group', help='Resource group of virtual network (default is web app resource group)')
            c.argument('http_headers', nargs='+', help="space-separated http headers in a format of `<name>=<value>`")
        with self.argument_context(scope + ' config access-restriction remove') as c:
            c.argument('name', arg_type=(webapp_name_arg_type if scope == 'webapp' else functionapp_name_arg_type))
            c.argument('rule_name', options_list=['--rule-name', '-r'],
                       help='Name of the access restriction to remove')
            c.argument('ip_address', help="IP address or CIDR range (optional comma separated list of up to 8 ranges)",
                       validator=validate_ip_address)
            c.argument('service_tag', help="Service Tag (optional comma separated list of up to 8 tags)",
                       validator=validate_service_tag)
            c.argument('vnet_name', help="vNet name")
            c.argument('subnet', help="Subnet name (requires vNet name) or subnet resource id")
            c.argument('scm_site', help='True if access restriction should be removed from scm site',
                       arg_type=get_three_state_flag())
            c.argument('action', arg_type=get_enum_type(ACCESS_RESTRICTION_ACTION_TYPES),
                       help="Allow or deny access")
        with self.argument_context(scope + ' config access-restriction set') as c:
            c.argument('name', arg_type=(webapp_name_arg_type if scope == 'webapp' else functionapp_name_arg_type))
            c.argument('use_same_restrictions_for_scm_site',
                       help="Use same access restrictions for scm site",
                       arg_type=get_three_state_flag())

    # App Service Environment Commands
    with self.argument_context('appservice ase show') as c:
        c.argument('name', options_list=['--name', '-n'], help='Name of the app service environment',
                   local_context_attribute=LocalContextAttribute(name='ase_name', actions=[LocalContextAction.GET]))
    with self.argument_context('appservice ase create') as c:
        c.argument('name', options_list=['--name', '-n'], validator=validate_ase_create,
                   help='Name of the app service environment',
                   local_context_attribute=LocalContextAttribute(name='ase_name', actions=[LocalContextAction.SET],
                                                                 scopes=['appservice']))
        c.argument('kind', options_list=['--kind', '-k'], arg_type=get_enum_type(ASE_KINDS),
                   default='ASEv2', help="Specify App Service Environment version")
        c.argument('subnet', help='Name or ID of existing subnet. To create vnet and/or subnet \
                   use `az network vnet [subnet] create`')
        c.argument('vnet_name', help='Name of the vNet. Mandatory if only subnet name is specified.')
        c.argument('virtual_ip_type', arg_type=get_enum_type(ASE_LOADBALANCER_MODES),
                   help="Specify if app service environment should be accessible from internet")
        c.argument('ignore_subnet_size_validation', arg_type=get_three_state_flag(),
                   help='Do not check if subnet is sized according to recommendations.')
        c.argument('ignore_route_table', arg_type=get_three_state_flag(),
                   help='Configure route table manually. Applies to ASEv2 only.')
        c.argument('ignore_network_security_group', arg_type=get_three_state_flag(),
                   help='Configure network security group manually. Applies to ASEv2 only.')
        c.argument('force_route_table', arg_type=get_three_state_flag(),
                   help='Override route table for subnet. Applies to ASEv2 only.')
        c.argument('force_network_security_group', arg_type=get_three_state_flag(),
                   help='Override network security group for subnet. Applies to ASEv2 only.')
        c.argument('front_end_scale_factor', type=int, validator=validate_front_end_scale_factor,
                   help='Scale of front ends to app service plan instance ratio. Applies to ASEv2 only.', default=15)
        c.argument('front_end_sku', arg_type=isolated_sku_arg_type, default='I1',
                   help='Size of front end servers. Applies to ASEv2 only.')
        c.argument('os_preference', arg_type=get_enum_type(ASE_OS_PREFERENCE_TYPES),
                   help='Determine if app service environment should start with Linux workers. Applies to ASEv2 only.')
        c.argument('zone_redundant', arg_type=get_three_state_flag(),
                   help='Configure App Service Environment as Zone Redundant. Applies to ASEv3 only.')
    with self.argument_context('appservice ase delete') as c:
        c.argument('name', options_list=['--name', '-n'], help='Name of the app service environment')
    with self.argument_context('appservice ase update') as c:
        c.argument('name', options_list=['--name', '-n'], help='Name of the app service environment',
                   local_context_attribute=LocalContextAttribute(name='ase_name', actions=[LocalContextAction.GET]))
        c.argument('front_end_scale_factor', type=int, validator=validate_front_end_scale_factor,
                   help='(ASEv2 only) Scale of front ends to app service plan instance ratio between 5 and 15.')
        c.argument('front_end_sku', arg_type=isolated_sku_arg_type,
                   help='(ASEv2 only) Size of front end servers.')
        c.argument('allow_new_private_endpoint_connections', arg_type=get_three_state_flag(),
                   options_list=['--allow-new-private-endpoint-connections', '-p'],
                   help='(ASEv3 only) Configure Apps in App Service Environment to allow new private endpoint connections.')
    with self.argument_context('appservice ase list-addresses') as c:
        c.argument('name', options_list=['--name', '-n'], help='Name of the app service environment',
                   local_context_attribute=LocalContextAttribute(name='ase_name', actions=[LocalContextAction.GET]))
    with self.argument_context('appservice ase list-plans') as c:
        c.argument('name', options_list=['--name', '-n'], help='Name of the app service environment',
                   local_context_attribute=LocalContextAttribute(name='ase_name', actions=[LocalContextAction.GET]))
    with self.argument_context('appservice ase create-inbound-services') as c:
        c.argument('name', options_list=['--name', '-n'], help='Name of the app service environment',
                   local_context_attribute=LocalContextAttribute(name='ase_name', actions=[LocalContextAction.GET]))
        c.argument('subnet', help='Name or ID of existing subnet for DNS Zone link. \
                   To create vnet and/or subnet use `az network vnet [subnet] create`')
        c.argument('vnet_name', help='Name of the vNet. Mandatory if only subnet name is specified.')
        c.argument('skip_dns', arg_type=get_three_state_flag(),
                   help='Do not create Private DNS Zone and DNS records.',
                   deprecate_info=c.deprecate(expiration='3.0.0'))

    # App Service Domain Commands
    with self.argument_context('appservice domain create') as c:
        c.argument('hostname', options_list=['--hostname', '-n'], help='Name of the custom domain')
        c.argument('contact_info', options_list=['--contact-info', '-c'], help='The file path to a JSON object with your contact info for domain registration. '
                                                                               'Please see the following link for the format of the JSON file expected: '
                                                                               'https://github.com/AzureAppServiceCLI/appservice_domains_templates/blob/master/contact_info.json')
        c.argument('privacy', options_list=['--privacy', '-p'], help='Enable privacy protection')
        c.argument('auto_renew', options_list=['--auto-renew', '-a'], help='Enable auto-renew on the domain')
        c.argument('accept_terms', options_list=['--accept-terms'], help='By using this flag, you are accepting '
                                                                         'the conditions shown using the --show-hostname-purchase-terms flag. ')
        c.argument('tags', arg_type=tags_type)
        c.argument('dryrun', help='Show summary of the purchase and create operation instead of executing it')
        c.argument('no_wait', help='Do not wait for the create to complete, and return immediately after queuing the create.')
        c.argument('validate', help='Generate and validate the ARM template without creating any resources')

    with self.argument_context('appservice domain show-terms') as c:
        c.argument('hostname', options_list=['--hostname', '-n'], help='Name of the custom domain')

    with self.argument_context('staticwebapp', validator=validate_public_cloud) as c:
        c.argument('source', options_list=['--source', '-s'], help="URL for the repository of the static site.", arg_group="Github")
        c.argument('token', options_list=['--token', '-t'], arg_group="Github",
                   help="A user's GitHub repository token. This is used to setup the Github Actions workflow file and "
                        "API secrets. If you need to create a Github Personal Access Token, "
                        "please run with the '--login-with-github' flag or follow the steps found at the following link:\n"
                        "https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line")
        c.argument('login_with_github', help="Interactively log in with Github to retrieve the Personal Access Token", arg_group="Github")
        c.argument('branch', options_list=['--branch', '-b'], help="The target branch in the repository.", arg_group="Github")
        c.ignore('format_output')
        c.argument('name', options_list=['--name', '-n'], metavar='NAME', help="Name of the static site")
    with self.argument_context('staticwebapp environment') as c:
        c.argument('environment_name',
                   options_list=['--environment-name'], help="Name of the environment of static site")
    with self.argument_context('staticwebapp hostname') as c:
        c.argument('hostname',
                   options_list=['--hostname'],
                   help="custom hostname such as www.example.com. Only support sub domain in preview.")
    with self.argument_context('staticwebapp hostname set') as c:
        c.argument('validation_method',
                   options_list=['--validation-method', '-m'],
                   help="Validation method for the custom domain.",
                   arg_type=get_enum_type(["cname-delegation", "dns-txt-token"]))
    with self.argument_context('staticwebapp appsettings') as c:
        c.argument('setting_pairs', options_list=['--setting-names'],
                   help="Space-separated app settings in 'key=value' format. ",
                   nargs='*')
        c.argument('setting_names', options_list=['--setting-names'], help="Space-separated app setting names.",
                   nargs='*')
    with self.argument_context('staticwebapp users') as c:
        c.argument('authentication_provider', options_list=['--authentication-provider'],
                   help="Authentication provider of the user identity such as AAD, Facebook, GitHub, Google, Twitter.")
        c.argument('user_details', options_list=['--user-details'],
                   help="Email for AAD, Facebook, and Google. Account name (handle) for GitHub and Twitter.")
        c.argument('user_id',
                   help="Given id of registered user.")
        c.argument('domain', options_list=['--domain'],
                   help="A domain added to the static app in quotes.")
        c.argument('roles', options_list=['--roles'],
                   help="Comma-separated default or user-defined role names. "
                        "Roles that can be assigned to a user are comma separated and case-insensitive (at most 50 "
                        "roles up to 25 characters each and restricted to 0-9,A-Z,a-z, and _). "
                        "Define roles in routes.json during root directory of your GitHub repo.")
        c.argument('invitation_expiration_in_hours', options_list=['--invitation-expiration-in-hours'],
                   help="This value sets when the link will expire in hours. The maximum is 168 (7 days).")
    with self.argument_context('staticwebapp identity') as c:
        c.argument('scope', help="The scope the managed identity has access to")
        c.argument('role', help="Role name or id the managed identity will be assigned")
    with self.argument_context('staticwebapp identity assign') as c:
        c.argument('assign_identities', options_list=['--identities'], nargs='*', help="Space-separated identities to assign. Use '{0}' to refer to the system assigned identity. Default: '{0}'".format(MSI_LOCAL_ID))
    with self.argument_context('staticwebapp identity remove') as c:
        c.argument('remove_identities', options_list=['--identities'], nargs='*', help="Space-separated identities to assign. Use '{0}' to refer to the system assigned identity. Default: '{0}'".format(MSI_LOCAL_ID))
    with self.argument_context('staticwebapp create') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('tags', arg_type=tags_type)
        c.argument('sku', arg_type=static_web_app_sku_arg_type)
        c.argument('app_location', options_list=['--app-location'],
                   help="Location of your application code. For example, '/' represents the root of your app, "
                        "while '/app' represents a directory called 'app'")
        c.argument('api_location', options_list=['--api-location'],
                   help="Location of your Azure Functions code. For example, '/api' represents a folder called 'api'.")
        c.argument('app_artifact_location', options_list=['--app-artifact-location'],
                   help="The path of your build output relative to your apps location. For example, setting a value "
                        "of 'build' when your app location is set to '/app' will cause the content at '/app/build' to "
                        "be served.",
                   deprecate_info=c.deprecate(expiration='2.22.1'))
        c.argument('output_location', options_list=['--output-location'],
                   help="The path of your build output relative to your apps location. For example, setting a value "
                        "of 'build' when your app location is set to '/app' will cause the content at '/app/build' to "
                        "be served.")
    with self.argument_context('staticwebapp update') as c:
        c.argument('tags', arg_type=tags_type)
        c.argument('sku', arg_type=static_web_app_sku_arg_type)
    with self.argument_context('staticwebapp functions link') as c:
        c.argument('function_resource_id', help="Resource ID of the functionapp to link. Can be retrieved with 'az functionapp --query id'")
        c.argument('force', help="Force the function link even if the function is already linked to a static webapp. May be needed if the function was previously linked to a static webapp.")
