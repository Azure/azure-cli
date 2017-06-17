# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import register_cli_argument
from azure.cli.core.util import shell_safe_json_parse
from azure.cli.core.cloud import get_clouds, get_custom_clouds, get_active_cloud_name

from azure.cli.core.profiles import API_PROFILES


def get_cloud_name_completion_list(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
    return [c.name for c in get_clouds()]


def get_custom_cloud_name_completion_list(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
    return [c.name for c in get_custom_clouds()]


active_cloud_name = get_active_cloud_name()

register_cli_argument('cloud', 'cloud_name', options_list=('--name', '-n'),
                      help='Name of a registered cloud',
                      completer=get_cloud_name_completion_list)

register_cli_argument('cloud show', 'cloud_name',
                      help='Name of a registered cloud.', default=active_cloud_name)
register_cli_argument('cloud update', 'cloud_name',
                      help='Name of a registered cloud.', default=active_cloud_name)
register_cli_argument('cloud list-profiles', 'cloud_name',
                      help='Name of a registered cloud.', default=active_cloud_name)
register_cli_argument('cloud list-profiles', 'show_all',
                      help='Show all available profiles supported in the CLI.', action='store_true')

register_cli_argument('cloud register', 'cloud_name', completer=None)

register_cli_argument('cloud unregister', 'cloud_name',
                      completer=get_custom_cloud_name_completion_list)

register_cli_argument('cloud', 'profile',
                      help='Profile to use for this cloud',
                      choices=list(API_PROFILES))

register_cli_argument('cloud', 'cloud_config', options_list=('--cloud-config',),
                      help='JSON encoded cloud configuration. Use @{file} to load from a file.',
                      type=shell_safe_json_parse)

register_cli_argument('cloud', 'endpoint_management',
                      help='The management service endpoint')
register_cli_argument('cloud', 'endpoint_resource_manager',
                      help='The resource management endpoint')
register_cli_argument('cloud', 'endpoint_sql_management',
                      help='The sql server management endpoint')
register_cli_argument('cloud', 'endpoint_gallery',
                      help='The template gallery endpoint')
register_cli_argument('cloud', 'endpoint_active_directory',
                      help='The Active Directory login endpoint')
register_cli_argument('cloud', 'endpoint_active_directory_resource_id',
                      help='The resource ID to obtain AD tokens for')
register_cli_argument('cloud', 'endpoint_active_directory_graph_resource_id',
                      help='The Active Directory resource ID')
register_cli_argument('cloud', 'suffix_sql_server_hostname',
                      help='The dns suffix for sql servers')
register_cli_argument('cloud', 'suffix_storage_endpoint',
                      help='The endpoint suffix for storage accounts')
register_cli_argument('cloud', 'suffix_keyvault_dns',
                      help='The Key Vault service dns suffix')
register_cli_argument('cloud', 'suffix_azure_datalake_store_file_system_endpoint',
                      help='The Data Lake store filesystem service dns suffix')
register_cli_argument('cloud', 'suffix_azure_datalake_analytics_catalog_and_job_endpoint',
                      help='The Data Lake analytics job and catalog service dns suffix')
