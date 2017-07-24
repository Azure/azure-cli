# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.util import shell_safe_json_parse
from azure.cli.core.cloud import get_clouds, get_custom_clouds, get_active_cloud_name
from azure.cli.core.profiles import API_PROFILES

from azure.cli.command_modules.cloud.custom import get_cloud_name_completion_list, get_custom_cloud_name_completion_list
import azure.cli.command_modules.cloud._help  # pylint: disable=unused-import


class CloudCommandsLoader(AzCommandsLoader):

    def load_command_table(self, args):
        super(CloudCommandsLoader, self).load_command_table(args)
        cloud_custom = 'azure.cli.command_modules.cloud.custom#'
        self.cli_command(__name__, 'cloud list', cloud_custom + 'list_clouds')
        self.cli_command(__name__, 'cloud show', cloud_custom + 'show_cloud')
        self.cli_command(__name__, 'cloud register', cloud_custom + 'register_cloud')
        self.cli_command(__name__, 'cloud unregister', cloud_custom + 'unregister_cloud')
        self.cli_command(__name__, 'cloud set', cloud_custom + 'set_cloud')
        self.cli_command(__name__, 'cloud update', cloud_custom + 'modify_cloud')
        self.cli_command(__name__, 'cloud list-profiles', cloud_custom + 'list_profiles')
        return self.command_table

    def load_arguments(self, command):
        active_cloud_name = self.ctx.cloud.name

        self.register_cli_argument('cloud', 'cloud_name', options_list=('--name', '-n'),
                                   help='Name of a registered cloud',
                                   completer=get_cloud_name_completion_list)

        self.register_cli_argument('cloud show', 'cloud_name',
                                   help='Name of a registered cloud.', default=active_cloud_name)
        self.register_cli_argument('cloud update', 'cloud_name',
                                   help='Name of a registered cloud.', default=active_cloud_name)
        self.register_cli_argument('cloud list-profiles', 'cloud_name',
                                   help='Name of a registered cloud.', default=active_cloud_name)
        self.register_cli_argument('cloud list-profiles', 'show_all',
                                   help='Show all available profiles supported in the CLI.', action='store_true')

        self.register_cli_argument('cloud register', 'cloud_name', completer=None)

        self.register_cli_argument('cloud unregister', 'cloud_name',
                                   completer=get_custom_cloud_name_completion_list)

        self.register_cli_argument('cloud', 'profile',
                                   help='Profile to use for this cloud',
                                   choices=list(API_PROFILES))

        self.register_cli_argument('cloud', 'cloud_config', options_list=('--cloud-config',),
                                   help='JSON encoded cloud configuration. Use @{file} to load from a file.',
                                   type=shell_safe_json_parse)

        self.register_cli_argument('cloud', 'endpoint_management',
                                   help='The management service endpoint')
        self.register_cli_argument('cloud', 'endpoint_resource_manager',
                                   help='The resource management endpoint')
        self.register_cli_argument('cloud', 'endpoint_sql_management',
                                   help='The sql server management endpoint')
        self.register_cli_argument('cloud', 'endpoint_gallery',
                                   help='The template gallery endpoint')
        self.register_cli_argument('cloud', 'endpoint_active_directory',
                                   help='The Active Directory login endpoint')
        self.register_cli_argument('cloud', 'endpoint_active_directory_resource_id',
                                   help='The resource ID to obtain AD tokens for')
        self.register_cli_argument('cloud', 'endpoint_active_directory_graph_resource_id',
                                   help='The Active Directory resource ID')
        self.register_cli_argument('cloud', 'endpoint_active_directory_data_lake_resource_id',
                                   help='The Active Directory resource ID for data lake services')
        self.register_cli_argument('cloud', 'endpoint_vm_image_alias_doc',
                                   help='The uri of the document which caches commonly used virtual machine images')
        self.register_cli_argument('cloud', 'suffix_sql_server_hostname',
                                   help='The dns suffix for sql servers')
        self.register_cli_argument('cloud', 'suffix_storage_endpoint',
                                   help='The endpoint suffix for storage accounts')
        self.register_cli_argument('cloud', 'suffix_keyvault_dns',
                                   help='The Key Vault service dns suffix')
        self.register_cli_argument('cloud', 'suffix_azure_datalake_store_file_system_endpoint',
                                   help='The Data Lake store filesystem service dns suffix')
        self.register_cli_argument('cloud', 'suffix_azure_datalake_analytics_catalog_and_job_endpoint',
                                   help='The Data Lake analytics job and catalog service dns suffix')
        super(CloudCommandsLoader, self).load_arguments(command)