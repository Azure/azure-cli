#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

CLIENT_ID = '04b07795-8ddb-461a-bbee-02f9e1bf7b46'

ENV_DEFAULT = 'AzureCloud'
ENV_US_GOVERNMENT = 'AzureUSGovernment'
ENV_CHINA = 'AzureChinaCloud'

COMMON_TENANT = 'common'

#ported from https://github.com/Azure/azure-xplat-cli/blob/dev/lib/util/profile/environment.js
class ENDPOINT_URLS: #pylint: disable=too-few-public-methods,old-style-class,no-init
    MANAGEMENT = 'management'
    ACTIVE_DIRECTORY_AUTHORITY = 'active_directory_authority'
    ACTIVE_DIRECTORY_GRAPH_RESOURCE_ID = 'active_directory_graph_resource_id'
    KEY_VAULT = 'key_vault'

_environments = {
    ENV_DEFAULT: {
        ENDPOINT_URLS.MANAGEMENT: 'https://management.core.windows.net/',
        ENDPOINT_URLS.ACTIVE_DIRECTORY_AUTHORITY : 'https://login.microsoftonline.com',
        ENDPOINT_URLS.ACTIVE_DIRECTORY_GRAPH_RESOURCE_ID: 'https://graph.windows.net/',
        ENDPOINT_URLS.KEY_VAULT: 'https://vault.azure.net'
        },
    ENV_CHINA: {
        ENDPOINT_URLS.MANAGEMENT: 'https://management.core.chinacloudapi.cn/',
        ENDPOINT_URLS.ACTIVE_DIRECTORY_AUTHORITY: 'https://login.chinacloudapi.cn',
        ENDPOINT_URLS.ACTIVE_DIRECTORY_GRAPH_RESOURCE_ID: 'https://graph.chinacloudapi.cn/',
        ENDPOINT_URLS.KEY_VAULT: 'https://vault.azure.cn'
        },
    ENV_US_GOVERNMENT: {
        ENDPOINT_URLS.MANAGEMENT: 'https://management.core.usgovcloudapi.net/',
        ENDPOINT_URLS.ACTIVE_DIRECTORY_AUTHORITY: 'https://login.microsoftonline.com',
        ENDPOINT_URLS.ACTIVE_DIRECTORY_GRAPH_RESOURCE_ID: 'https://graph.windows.net/',
        ENDPOINT_URLS.KEY_VAULT: 'https://vault.usgovcloudapi.net'
        }
}

def get_env(env_name=None):
    if env_name is None:
        env_name = ENV_DEFAULT
    elif env_name not in _environments:
        raise ValueError
    return _environments[env_name]

def get_authority_url(tenant=None, env_name=None):
    env = get_env(env_name)
    return env[ENDPOINT_URLS.ACTIVE_DIRECTORY_AUTHORITY] + '/' + (tenant or COMMON_TENANT)
