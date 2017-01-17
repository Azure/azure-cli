# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

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


class CloudEndpointNotSetException(Exception):
    pass


class CloudSuffixNotSetException(Exception):
    pass


class CloudEndpoints(object):  # pylint: disable=too-few-public-methods

    def __init__(self,  # pylint: disable=too-many-arguments
                 management=None,
                 resource_manager=None,
                 sql_management=None,
                 gallery=None,
                 active_directory=None,
                 active_directory_resource_id=None,
                 active_directory_graph_resource_id=None):
        # Attribute names are significant. They are used when storing/retrieving clouds from config
        self.management = management
        self.resource_manager = resource_manager
        self.sql_management = sql_management
        self.gallery = gallery
        self.active_directory = active_directory
        self.active_directory_resource_id = active_directory_resource_id
        self.active_directory_graph_resource_id = active_directory_graph_resource_id

    def __getattribute__(self, name):
        val = object.__getattribute__(self, name)
        if val is None:
            raise CloudEndpointNotSetException("The endpoint '{}' for this cloud "
                                               "is not set but is used".format(name))
        return val


class CloudSuffixes(object):  # pylint: disable=too-few-public-methods

    def __init__(self,  # pylint: disable=too-many-arguments
                 storage_endpoint=None,
                 keyvault_dns=None,
                 sql_server_hostname=None,
                 azure_datalake_store_file_system_endpoint=None,
                 azure_datalake_analytics_catalog_and_job_endpoint=None):
        # Attribute names are significant. They are used when storing/retrieving clouds from config
        self.storage_endpoint = storage_endpoint
        self.keyvault_dns = keyvault_dns
        self.sql_server_hostname = sql_server_hostname
        self.azure_datalake_store_file_system_endpoint = azure_datalake_store_file_system_endpoint
        self.azure_datalake_analytics_catalog_and_job_endpoint = azure_datalake_analytics_catalog_and_job_endpoint  # pylint: disable=line-too-long

    def __getattribute__(self, name):
        val = object.__getattribute__(self, name)
        if val is None:
            raise CloudSuffixNotSetException("The suffix '{}' for this cloud "
                                             "is not set but is used".format(name))
        return val


class Cloud(object):  # pylint: disable=too-few-public-methods
    """ Represents an Azure Cloud instance """

    def __init__(self, name, endpoints=None, suffixes=None):
        self.name = name
        self.endpoints = endpoints or CloudEndpoints()
        self.suffixes = suffixes or CloudSuffixes()


AZURE_PUBLIC_CLOUD = Cloud(
    'AzureCloud',
    endpoints=CloudEndpoints(
        management='https://management.core.windows.net/',
        resource_manager='https://management.azure.com/',
        sql_management='https://management.core.windows.net:8443/',
        gallery='https://gallery.azure.com/',
        active_directory='https://login.microsoftonline.com',
        active_directory_resource_id='https://management.core.windows.net/',
        active_directory_graph_resource_id='https://graph.windows.net/'),
    suffixes=CloudSuffixes(
        storage_endpoint='core.windows.net',
        keyvault_dns='.vault.azure.net',
        sql_server_hostname='.database.windows.net',
        azure_datalake_store_file_system_endpoint='azuredatalakestore.net',
        azure_datalake_analytics_catalog_and_job_endpoint='azuredatalakeanalytics.net'))

AZURE_CHINA_CLOUD = Cloud(
    'AzureChinaCloud',
    endpoints=CloudEndpoints(
        management='https://management.core.chinacloudapi.cn/',
        resource_manager='https://management.chinacloudapi.cn',
        sql_management='https://management.core.chinacloudapi.cn:8443/',
        gallery='https://gallery.chinacloudapi.cn/',
        active_directory='https://login.chinacloudapi.cn',
        active_directory_resource_id='https://management.core.chinacloudapi.cn/',
        active_directory_graph_resource_id='https://graph.chinacloudapi.cn/'),
    suffixes=CloudSuffixes(
        storage_endpoint='core.chinacloudapi.cn',
        keyvault_dns='.vault.azure.cn',
        sql_server_hostname='.database.chinacloudapi.cn'))

AZURE_US_GOV_CLOUD = Cloud(
    'AzureUSGovernment',
    endpoints=CloudEndpoints(
        management='https://management.core.usgovcloudapi.net/',
        resource_manager='https://management.usgovcloudapi.net/',
        sql_management='https://management.core.usgovcloudapi.net:8443/',
        gallery='https://gallery.usgovcloudapi.net/',
        active_directory='https://login.microsoftonline.com',
        active_directory_resource_id='https://management.core.usgovcloudapi.net/',
        active_directory_graph_resource_id='https://graph.windows.net/'),
    suffixes=CloudSuffixes(
        storage_endpoint='core.usgovcloudapi.net',
        keyvault_dns='.vault.usgovcloudapi.net',
        sql_server_hostname='.database.usgovcloudapi.net'))

AZURE_GERMAN_CLOUD = Cloud(
    'AzureGermanCloud',
    endpoints=CloudEndpoints(
        management='https://management.core.cloudapi.de/',
        resource_manager='https://management.microsoftazure.de',
        sql_management='https://management.core.cloudapi.de:8443/',
        gallery='https://gallery.cloudapi.de/',
        active_directory='https://login.microsoftonline.de',
        active_directory_resource_id='https://management.core.cloudapi.de/',
        active_directory_graph_resource_id='https://graph.cloudapi.de/'),
    suffixes=CloudSuffixes(
        storage_endpoint='core.cloudapi.de',
        keyvault_dns='.vault.microsoftazure.de',
        sql_server_hostname='.database.cloudapi.de'))

KNOWN_CLOUDS = [AZURE_PUBLIC_CLOUD, AZURE_CHINA_CLOUD, AZURE_US_GOV_CLOUD, AZURE_GERMAN_CLOUD]


def _get_cloud(cloud_name):
    return next((x for x in get_clouds() if x.name == cloud_name), None)


def get_custom_clouds():
    clouds = []
    config = configparser.SafeConfigParser()
    config.read(CUSTOM_CLOUD_CONFIG_FILE)
    for section in config.sections():
        c = Cloud(section)
        for option in config.options(section):
            if option.startswith('endpoint_'):
                setattr(c.endpoints, option.replace('endpoint_', ''), config.get(section, option))
            elif option.startswith('suffix_'):
                setattr(c.suffixes, option.replace('suffix_', ''), config.get(section, option))
        clouds.append(c)
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
    for k, v in cloud.endpoints.__dict__.items():
        if v:
            config.set(cloud.name, 'endpoint_{}'.format(k), v)
    for k, v in cloud.suffixes.__dict__.items():
        if v:
            config.set(cloud.name, 'suffix_{}'.format(k), v)
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
        raise CannotUnregisterCloudException("The cloud '{}' cannot be unregistered "
                                             "as it's not a custom cloud.".format(cloud_name))
    contexts_using_cloud = [context for context in get_contexts() if context.get(
        'cloud', None) == cloud_name]  # pylint: disable=line-too-long
    if contexts_using_cloud:
        context_names = [context['name'] for context in contexts_using_cloud]
        many_contexts = len(context_names) > 1
        raise CannotUnregisterCloudException(
            "The cloud '{0}' is in use by the following context{1} '{2}'.".format(
                cloud_name,
                's' if many_contexts else '',
                ', '.join(context_names)))
    config = configparser.SafeConfigParser()
    config.read(CUSTOM_CLOUD_CONFIG_FILE)
    config.remove_section(cloud_name)
    with open(CUSTOM_CLOUD_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
