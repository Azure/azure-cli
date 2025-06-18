# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.util import shell_safe_json_parse
from azure.cli.core.profiles import API_PROFILES
from azure.cli.core.commands import CliCommandType

from azure.cli.command_modules.cloud._completers import (
    get_cloud_name_completion_list, get_custom_cloud_name_completion_list)
import azure.cli.command_modules.cloud._help  # pylint: disable=unused-import


class CloudCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        super().__init__(cli_ctx=cli_ctx)

    def load_command_table(self, args):

        cloud_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.cloud.custom#{}')

        with self.command_group('cloud', cloud_custom) as g:
            g.command('list', 'list_clouds')
            g.show_command('show', 'show_cloud')
            g.command('register', 'register_cloud')
            g.command('unregister', 'unregister_cloud')
            g.command('set', 'set_cloud')
            g.command('update', 'modify_cloud')
            g.command('list-profiles', 'list_profiles')

        return self.command_table

    def load_arguments(self, command):

        active_cloud_name = self.cli_ctx.cloud.name

        # pylint: disable=line-too-long
        with self.argument_context('cloud') as c:
            c.argument('cloud_name', options_list=('--name', '-n'), help='Name of a registered cloud', completer=get_cloud_name_completion_list)
            c.argument('profile', help='Profile to use for this cloud. The azure stack profiles `2017-03-09-profile` `2018-03-01-hybrid` `2019-03-01-hybrid` and `2020-09-01-hybrid` have been deprecated and removed. To continue using Azure Stack, please install the Azure CLI `2.66.*` (LTS) version. For more details, refer to: https://learn.microsoft.com/en-us/cli/azure/whats-new-overview#important-notice-for-azure-stack-hub-customers', choices=list(API_PROFILES))
            c.argument('cloud_config', options_list=('--cloud-config',), help='JSON encoded cloud configuration. Use @{file} to load from a file.', type=shell_safe_json_parse)
            c.argument('skip_endpoint_discovery', action='store_true', help="If specified, the cloud endpoints' auto discovery will be skipped")
            c.argument('endpoint_management', help='The management service endpoint')
            c.argument('endpoint_resource_manager', help='The resource management endpoint')
            c.argument('endpoint_sql_management', help='The sql server management endpoint')
            c.argument('endpoint_gallery', help='The template gallery endpoint')
            c.argument('endpoint_active_directory', help='The Active Directory login endpoint')
            c.argument('endpoint_active_directory_resource_id', help='The resource ID to obtain AD tokens for')
            c.argument('endpoint_active_directory_graph_resource_id', help='The Active Directory resource ID')
            c.argument('endpoint_microsoft_graph_resource_id', help='The Microsoft Graph resource ID')
            c.argument('endpoint_active_directory_data_lake_resource_id', help='The Active Directory resource ID for data lake services')
            c.argument('endpoint_vm_image_alias_doc', help='The uri of the document which caches commonly used virtual machine images')
            c.argument('suffix_sql_server_hostname', help='The dns suffix for sql servers')
            c.argument('suffix_storage_endpoint', help='The endpoint suffix for storage accounts')
            c.argument('suffix_keyvault_dns', help='The Key Vault service dns suffix')
            c.argument('suffix_azure_datalake_store_file_system_endpoint', help='The Data Lake store filesystem service dns suffix')
            c.argument('suffix_azure_datalake_analytics_catalog_and_job_endpoint', help='The Data Lake analytics job and catalog service dns suffix')
            c.argument('suffix_acr_login_server_endpoint', help='The Azure Container Registry login server suffix')
            c.ignore('_subscription')  # hide global subscription param

        with self.argument_context('cloud show') as c:
            c.argument('cloud_name', help='Name of a registered cloud.', default=active_cloud_name)

        with self.argument_context('cloud update') as c:
            c.argument('cloud_name', help='Name of a registered cloud.', default=active_cloud_name)

        with self.argument_context('cloud list-profiles') as c:
            c.argument('cloud_name', help='Name of a registered cloud.', default=active_cloud_name)
            c.argument('show_all', help='Show all available profiles supported in the CLI.', action='store_true')

        with self.argument_context('cloud register') as c:
            c.argument('cloud_name', completer=None)

        with self.argument_context('cloud unregister') as c:
            c.argument('cloud_name', completer=get_custom_cloud_name_completion_list)


COMMAND_LOADER_CLS = CloudCommandsLoader
