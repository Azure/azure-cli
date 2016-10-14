#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import os
from six.moves import configparser

from azure.cli.core._config import GLOBAL_CONFIG_DIR

CUSTOM_CLOUD_CONFIG_FILE = os.path.join(GLOBAL_CONFIG_DIR, 'clouds.config')

class CloudNotRegisteredException(Exception):
    def __init__(self, cloud_name):
        super(CloudNotRegisteredException, self).__init__(cloud_name)
        self.cloud_name = cloud_name
    def __str__(self):
        return "The cloud '{}' is not registered.".format(self.cloud_name)

class CloudAlreadyRegisteredException(Exception):
    def __init__(self, cloud_name):
        super(CloudAlreadyRegisteredException, self).__init__(cloud_name)
        self.cloud_name = cloud_name
    def __str__(self):
        return "The cloud '{}' is already registered.".format(self.cloud_name)

class CannotUnregisterCloudException(Exception):
    pass

class CloudEndpointUrl(object): # pylint: disable=too-few-public-methods
    MANAGEMENT = 'management'
    RESOURCE_MANAGER = 'resource_manager'
    SQL_MANAGEMENT = 'sql_management'
    GALLERY = 'gallery'
    ACTIVE_DIRECTORY = 'active_directory'
    ACTIVE_DIRECTORY_RESOURCE_ID = 'active_directory_resource_id'
    ACTIVE_DIRECTORY_GRAPH_RESOURCE_ID = 'active_directory_graph_resource_id'

class CloudParam(object): # pylint: disable=too-few-public-methods
    SQL_SERVER_HOSTNAME_SUFFIX = 'sql_server_hostname_suffix'
    STORAGE_ENDPOINT_SUFFIX = 'storage_endpoint_suffix'
    KEYVAULT_DNS_SUFFIX = 'keyvault_dns_suffix'
    AZURE_DATALAKE_STORE_FILE_SYSTEM_ENDPOINT_SUFFIX = 'azure_datalake_store_file_system_endpoint_suffix' #pylint: disable=line-too-long
    AZURE_DATALAKE_ANALYTICS_CATALOG_AND_JOB_ENDPOINT_SUFFIX = 'azure_datalake_analytics_catalog_and_job_endpoint_suffix' #pylint: disable=line-too-long

class Cloud(object): # pylint: disable=too-few-public-methods
    """ Represents an Azure Cloud instance """

    def __init__(self, name, endpoints=None, params=None):
        self.name = name
        self.endpoints = endpoints
        self.params = params

AZURE_PUBLIC_CLOUD = Cloud('AzureCloud', endpoints={
    CloudEndpointUrl.MANAGEMENT: 'https://management.core.windows.net/',
    CloudEndpointUrl.RESOURCE_MANAGER: 'https://management.azure.com/',
    CloudEndpointUrl.SQL_MANAGEMENT: 'https://management.core.windows.net:8443/',
    CloudEndpointUrl.GALLERY: 'https://gallery.azure.com/',
    CloudEndpointUrl.ACTIVE_DIRECTORY: 'https://login.microsoftonline.com',
    CloudEndpointUrl.ACTIVE_DIRECTORY_RESOURCE_ID: 'https://management.core.windows.net/',
    CloudEndpointUrl.ACTIVE_DIRECTORY_GRAPH_RESOURCE_ID: 'https://graph.windows.net/'
    }, params={
        CloudParam.SQL_SERVER_HOSTNAME_SUFFIX: '.database.windows.net',
        CloudParam.STORAGE_ENDPOINT_SUFFIX: '.core.windows.net',
        CloudParam.KEYVAULT_DNS_SUFFIX: '.vault.azure.net',
        CloudParam.AZURE_DATALAKE_STORE_FILE_SYSTEM_ENDPOINT_SUFFIX: 'azuredatalakestore.net',
        CloudParam.AZURE_DATALAKE_ANALYTICS_CATALOG_AND_JOB_ENDPOINT_SUFFIX: 'azuredatalakeanalytics.net' #pylint: disable=line-too-long
    })

AZURE_CHINA_CLOUD = Cloud('AzureChinaCloud', endpoints={
    CloudEndpointUrl.MANAGEMENT: 'https://management.core.chinacloudapi.cn/',
    CloudEndpointUrl.RESOURCE_MANAGER: 'https://management.chinacloudapi.cn',
    CloudEndpointUrl.SQL_MANAGEMENT: 'https://management.core.chinacloudapi.cn:8443/',
    CloudEndpointUrl.GALLERY: 'https://gallery.chinacloudapi.cn/',
    CloudEndpointUrl.ACTIVE_DIRECTORY: 'https://login.chinacloudapi.cn',
    CloudEndpointUrl.ACTIVE_DIRECTORY_RESOURCE_ID: 'https://management.core.chinacloudapi.cn/',
    CloudEndpointUrl.ACTIVE_DIRECTORY_GRAPH_RESOURCE_ID: 'https://graph.chinacloudapi.cn/'
    }, params={
        CloudParam.SQL_SERVER_HOSTNAME_SUFFIX: '.database.chinacloudapi.cn',
        CloudParam.STORAGE_ENDPOINT_SUFFIX: '.core.chinacloudapi.cn',
        CloudParam.KEYVAULT_DNS_SUFFIX: '.vault.azure.cn'
    })

AZURE_US_GOV_CLOUD = Cloud('AzureUSGovernment', endpoints={
    CloudEndpointUrl.MANAGEMENT: 'https://management.core.usgovcloudapi.net',
    CloudEndpointUrl.RESOURCE_MANAGER: 'https://management.usgovcloudapi.net',
    CloudEndpointUrl.SQL_MANAGEMENT: 'https://management.core.usgovcloudapi.net:8443/',
    CloudEndpointUrl.GALLERY: 'https://gallery.usgovcloudapi.net/',
    CloudEndpointUrl.ACTIVE_DIRECTORY: 'https://login.microsoftonline.com',
    CloudEndpointUrl.ACTIVE_DIRECTORY_RESOURCE_ID: 'https://management.core.usgovcloudapi.net/',
    CloudEndpointUrl.ACTIVE_DIRECTORY_GRAPH_RESOURCE_ID: 'https://graph.windows.net/'
    }, params={
        CloudParam.SQL_SERVER_HOSTNAME_SUFFIX: '.database.usgovcloudapi.net',
        CloudParam.STORAGE_ENDPOINT_SUFFIX: '.core.usgovcloudapi.net',
        CloudParam.KEYVAULT_DNS_SUFFIX: '.vault.usgovcloudapi.net'
    })

AZURE_GERMAN_CLOUD = Cloud('AzureGermanCloud', endpoints={
    CloudEndpointUrl.MANAGEMENT: 'https://management.core.cloudapi.de',
    CloudEndpointUrl.RESOURCE_MANAGER: 'https://management.microsoftazure.de',
    CloudEndpointUrl.SQL_MANAGEMENT: 'https://management.core.cloudapi.de:8443/',
    CloudEndpointUrl.GALLERY: 'https://gallery.cloudapi.de/',
    CloudEndpointUrl.ACTIVE_DIRECTORY: 'https://login.microsoftonline.de',
    CloudEndpointUrl.ACTIVE_DIRECTORY_RESOURCE_ID: 'https://management.core.cloudapi.de/',
    CloudEndpointUrl.ACTIVE_DIRECTORY_GRAPH_RESOURCE_ID: 'https://graph.cloudapi.de/'
    }, params={
        CloudParam.SQL_SERVER_HOSTNAME_SUFFIX: '.database.cloudapi.de',
        CloudParam.STORAGE_ENDPOINT_SUFFIX: '.core.cloudapi.de',
        CloudParam.KEYVAULT_DNS_SUFFIX: '.vault.microsoftazure.de'
    })

KNOWN_CLOUDS = [AZURE_PUBLIC_CLOUD, AZURE_CHINA_CLOUD, AZURE_US_GOV_CLOUD, AZURE_GERMAN_CLOUD]

_get_cloud = lambda cloud_name: next((x for x in get_clouds() if x.name == cloud_name), None)

def get_custom_clouds():
    clouds = []
    config = configparser.SafeConfigParser()
    config.read(CUSTOM_CLOUD_CONFIG_FILE)
    for section in config.sections():
        cloud_to_add = Cloud(section, endpoints={}, params={})
        for option in config.options(section):
            if option.startswith('endpoint_url_'):
                cloud_to_add.endpoints[option.replace('endpoint_url_', '')] = config.get(section, option) # pylint: disable=line-too-long
            elif option.startswith('param_'):
                cloud_to_add.params[option.replace('param_', '')] = config.get(section, option)
        clouds.append(cloud_to_add)
    # print(clouds)
    return clouds

def get_clouds():
    clouds = KNOWN_CLOUDS[:]
    clouds.extend(get_custom_clouds())
    return clouds

def get_cloud(cloud_name):
    cloud = _get_cloud(cloud_name)
    if not cloud:
        raise CloudNotRegisteredException(cloud_name)
    return cloud

def add_cloud(cloud):
    if _get_cloud(cloud.name):
        raise CloudAlreadyRegisteredException(cloud.name)
    config = configparser.SafeConfigParser()
    config.read(CUSTOM_CLOUD_CONFIG_FILE)
    try:
        config.add_section(cloud.name)
    except configparser.DuplicateSectionError:
        raise CloudAlreadyRegisteredException(cloud.name)
    for endpoint in cloud.endpoints:
        if cloud.endpoints[endpoint]:
            config.set(cloud.name, 'endpoint_url_{}'.format(endpoint), cloud.endpoints[endpoint])
    for param in cloud.params:
        if cloud.params[param]:
            config.set(cloud.name, 'param_{}'.format(param), cloud.params[param])
    if not os.path.isdir(GLOBAL_CONFIG_DIR):
        os.makedirs(GLOBAL_CONFIG_DIR)
    with open(CUSTOM_CLOUD_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def remove_cloud(cloud_name):
    from azure.cli.core.context import get_contexts
    if not _get_cloud(cloud_name):
        raise CloudNotRegisteredException(cloud_name)
    is_known_cloud = next((x for x in KNOWN_CLOUDS if x.name == cloud_name), None)
    if is_known_cloud:
        raise CannotUnregisterCloudException("The cloud '{}' cannot be unregistered as it's not a custom cloud.".format(cloud_name)) #pylint: disable=line-too-long
    contexts_using_cloud = [context for context in get_contexts() if context.get('cloud', None) == cloud_name] #pylint: disable=line-too-long
    if contexts_using_cloud:
        context_names = [context['name'] for context in contexts_using_cloud]
        many_contexts = len(context_names) > 1
        raise CannotUnregisterCloudException("The cloud '{0}' is in use by the following context{1} '{2}'.".format( #pylint: disable=line-too-long
            cloud_name,
            's' if many_contexts else '',
            ', '.join(context_names)))
    config = configparser.SafeConfigParser()
    config.read(CUSTOM_CLOUD_CONFIG_FILE)
    config.remove_section(cloud_name)
    with open(CUSTOM_CLOUD_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
