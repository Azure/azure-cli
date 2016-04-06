CLIENT_ID = '04b07795-8ddb-461a-bbee-02f9e1bf7b46'

ENV_DEFAULT = 'AzureCloud'
ENV_US_GOVERNMENT = 'AzureUSGovernment'
ENV_CHINA = 'AzureChinaCloud'

COMMON_TENANT = 'common'

#ported from https://github.com/Azure/azure-xplat-cli/blob/dev/lib/util/profile/environment.js
class ENDPOINT_URLS: #pylint: disable=too-few-public-methods,old-style-class,no-init
    MANAGEMENT = 'management'
    ACTIVE_DIRECTORY_AUTHORITY = 'active_directory_authority'

_environments = {
    ENV_DEFAULT: {
        ENDPOINT_URLS.MANAGEMENT: 'https://management.core.windows.net/',
        ENDPOINT_URLS.ACTIVE_DIRECTORY_AUTHORITY : 'https://login.microsoftonline.com'
        },
    ENV_CHINA: {
        ENDPOINT_URLS.MANAGEMENT: 'https://management.core.chinacloudapi.cn/',
        ENDPOINT_URLS.ACTIVE_DIRECTORY_AUTHORITY: 'https://login.chinacloudapi.cn'
        },
    ENV_US_GOVERNMENT: {
        ENDPOINT_URLS.MANAGEMENT: 'https://management.core.usgovcloudapi.net/',
        ENDPOINT_URLS.ACTIVE_DIRECTORY_AUTHORITY: 'https://login.microsoftonline.com'
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

def get_management_endpoint_url(env_name=None):
    env = get_env(env_name)
    return env[ENDPOINT_URLS.MANAGEMENT]

