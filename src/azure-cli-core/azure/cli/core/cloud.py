# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from pprint import pformat
from six.moves import configparser

from azure.cli.core.profiles import API_PROFILES
from azure.cli.core._config import GLOBAL_CONFIG_DIR, GLOBAL_CONFIG_PATH

from knack.log import get_logger
from knack.util import CLIError
from knack.config import get_config_parser

logger = get_logger(__name__)

CLOUD_CONFIG_FILE = os.path.join(GLOBAL_CONFIG_DIR, 'clouds.config')


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


class CloudEndpointNotSetException(CLIError):
    pass


class CloudSuffixNotSetException(CLIError):
    pass


class CloudEndpoints(object):  # pylint: disable=too-few-public-methods,too-many-instance-attributes

    def __init__(self,
                 management=None,
                 resource_manager=None,
                 sql_management=None,
                 batch_resource_id=None,
                 gallery=None,
                 active_directory=None,
                 active_directory_resource_id=None,
                 active_directory_graph_resource_id=None,
                 active_directory_data_lake_resource_id=None,
                 vm_image_alias_doc=None):
        # Attribute names are significant. They are used when storing/retrieving clouds from config
        self.management = management
        self.resource_manager = resource_manager
        self.sql_management = sql_management
        self.batch_resource_id = batch_resource_id
        self.gallery = gallery
        self.active_directory = active_directory
        self.active_directory_resource_id = active_directory_resource_id
        self.active_directory_graph_resource_id = active_directory_graph_resource_id
        self.active_directory_data_lake_resource_id = active_directory_data_lake_resource_id
        self.vm_image_alias_doc = vm_image_alias_doc

    def has_endpoint_set(self, endpoint_name):
        try:
            # Can't simply use hasattr here as we override __getattribute__ below.
            # Python 3 hasattr() only returns False if an AttributeError is raised but we raise
            # CloudEndpointNotSetException. This exception is not a subclass of AttributeError.
            getattr(self, endpoint_name)
            return True
        except Exception:  # pylint: disable=broad-except
            return False

    def __getattribute__(self, name):
        val = object.__getattribute__(self, name)
        if val is None:
            raise CloudEndpointNotSetException("The endpoint '{}' for this cloud "
                                               "is not set but is used.".format(name))
        return val


class CloudSuffixes(object):  # pylint: disable=too-few-public-methods

    def __init__(self,
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
        self.azure_datalake_analytics_catalog_and_job_endpoint = azure_datalake_analytics_catalog_and_job_endpoint

    def __getattribute__(self, name):
        val = object.__getattribute__(self, name)
        if val is None:
            raise CloudSuffixNotSetException("The suffix '{}' for this cloud "
                                             "is not set but is used.".format(name))
        return val


class Cloud(object):  # pylint: disable=too-few-public-methods
    """ Represents an Azure Cloud instance """

    def __init__(self,
                 name,
                 endpoints=None,
                 suffixes=None,
                 profile=None,
                 is_active=False):
        self.name = name
        self.endpoints = endpoints or CloudEndpoints()
        self.suffixes = suffixes or CloudSuffixes()
        self.profile = profile
        self.is_active = is_active

    def __str__(self):
        o = {
            'profile': self.profile,
            'name': self.name,
            'is_active': self.is_active,
            'endpoints': vars(self.endpoints),
            'suffixes': vars(self.suffixes),
        }
        return pformat(o)

    def get_api_version(self, resource_type):
        """ Get the current API version for a given resource_type.

        :param resource_type: The resource type.
        :type resource_type: ResourceType.
        :returns:  str -- The API version.
        """
        from azure.cli.core.profiles._shared import get_api_version as _sdk_get_api_version
        return _sdk_get_api_version(self.profile, resource_type)

    def supported_api_version(self, resource_type, min_api=None, max_api=None):
        """ Method to check if the current API version for a given resource_type is supported.
            If resource_type is set to None, the current profile version will be used as the basis of
            the comparison.

        :param resource_type: The resource type.
        :type resource_type: ResourceType.
        :param min_api: The minimum API that is supported (inclusive). Omit for no minimum constraint.
        "type min_api: str
        :param max_api: The maximum API that is supported (inclusive). Omit for no maximum constraint.
        "type max_api: str
        :returns:  bool -- True if the current API version of resource_type satisfies the
                           min/max constraints. False otherwise.
        """
        from azure.cli.core.profiles._shared import supported_api_version as _sdk_supported_api_version
        return _sdk_supported_api_version(self.profile, resource_type, min_api, max_api)

    def get_sdk(self, resource_type, *attr_args, **kwargs):
        """ Get any SDK object that's versioned using the current API version for resource_type.
            Supported keyword arguments:
                checked - A boolean specifying if this method should suppress/check import exceptions
                          or not. By default, None is returned.
                mod - A string specifying the submodule that all attr_args should be prefixed with.

            Example usage:
                Get a single SDK model.
                TableService = get_sdk(resource_type, 'table#TableService')

                File, Directory = get_sdk(resource_type,
                                          'file.models#File',
                                          'file.models#Directory')

                Same as above but get multiple models where File and Directory are both part of
                'file.models' and we don't want to specify each full path.
                File, Directory = get_sdk(resource_type,
                                          'File',
                                          'Directory',
                                          mod='file.models')

        :param resource_type: The resource type.
        :type resource_type: ResourceType.
        :param attr_args: Positional arguments for paths to objects to get.
        :type attr_args: str
        :param kwargs: Keyword arguments.
        :type kwargs: str
        :returns: object -- e.g. an SDK module, model, enum, attribute. The number of objects returned
                            depends on len(attr_args).
        """
        from azure.cli.core.profiles._shared import get_versioned_sdk as _sdk_get_versioned_sdk
        return _sdk_get_versioned_sdk(self.profile, resource_type, *attr_args, **kwargs)


AZURE_PUBLIC_CLOUD = Cloud(
    'AzureCloud',
    endpoints=CloudEndpoints(
        management='https://management.core.windows.net/',
        resource_manager='https://management.azure.com/',
        sql_management='https://management.core.windows.net:8443/',
        batch_resource_id='https://batch.core.windows.net/',
        gallery='https://gallery.azure.com/',
        active_directory='https://login.microsoftonline.com',
        active_directory_resource_id='https://management.core.windows.net/',
        active_directory_graph_resource_id='https://graph.windows.net/',
        active_directory_data_lake_resource_id='https://datalake.azure.net/',
        vm_image_alias_doc='https://raw.githubusercontent.com/Azure/azure-rest-api-specs/master/arm-compute/quickstart-templates/aliases.json'),  # pylint: disable=line-too-long
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
        batch_resource_id='https://batch.chinacloudapi.cn/',
        gallery='https://gallery.chinacloudapi.cn/',
        active_directory='https://login.chinacloudapi.cn',
        active_directory_resource_id='https://management.core.chinacloudapi.cn/',
        active_directory_graph_resource_id='https://graph.chinacloudapi.cn/',
        vm_image_alias_doc='https://raw.githubusercontent.com/Azure/azure-rest-api-specs/master/arm-compute/quickstart-templates/aliases.json'),  # pylint: disable=line-too-long
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
        batch_resource_id='https://batch.core.usgovcloudapi.net/',
        gallery='https://gallery.usgovcloudapi.net/',
        active_directory='https://login.microsoftonline.com',
        active_directory_resource_id='https://management.core.usgovcloudapi.net/',
        active_directory_graph_resource_id='https://graph.windows.net/',
        vm_image_alias_doc='https://raw.githubusercontent.com/Azure/azure-rest-api-specs/master/arm-compute/quickstart-templates/aliases.json'),   # pylint: disable=line-too-long
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
        batch_resource_id='https://batch.cloudapi.de/',
        gallery='https://gallery.cloudapi.de/',
        active_directory='https://login.microsoftonline.de',
        active_directory_resource_id='https://management.core.cloudapi.de/',
        active_directory_graph_resource_id='https://graph.cloudapi.de/',
        vm_image_alias_doc='https://raw.githubusercontent.com/Azure/azure-rest-api-specs/master/arm-compute/quickstart-templates/aliases.json'),  # pylint: disable=line-too-long
    suffixes=CloudSuffixes(
        storage_endpoint='core.cloudapi.de',
        keyvault_dns='.vault.microsoftazure.de',
        sql_server_hostname='.database.cloudapi.de'))


KNOWN_CLOUDS = [AZURE_PUBLIC_CLOUD, AZURE_CHINA_CLOUD, AZURE_US_GOV_CLOUD, AZURE_GERMAN_CLOUD]


def _set_active_cloud(cli_ctx, cloud_name):
    cli_ctx.config.set_value('cloud', 'name', cloud_name)


def get_active_cloud_name(cli_ctx):
    try:
        return cli_ctx.config.config_parser.get('cloud', 'name')
    except (configparser.NoOptionError, configparser.NoSectionError):
        _set_active_cloud(cli_ctx, AZURE_PUBLIC_CLOUD.name)
        return AZURE_PUBLIC_CLOUD.name


def _get_cloud(cli_ctx, cloud_name):
    return next((x for x in get_clouds(cli_ctx) if x.name == cloud_name), None)


def get_custom_clouds():
    known_cloud_names = [c.name for c in KNOWN_CLOUDS]
    return [c for c in get_clouds() if c.name not in known_cloud_names]


def init_known_clouds(force=False):
    config = get_config_parser()
    config.read(CLOUD_CONFIG_FILE)
    stored_cloud_names = config.sections()
    for c in KNOWN_CLOUDS:
        if force or c.name not in stored_cloud_names:
            _config_add_cloud(config, c, overwrite=force)
    if not os.path.isdir(GLOBAL_CONFIG_DIR):
        os.makedirs(GLOBAL_CONFIG_DIR)
    with open(CLOUD_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def get_clouds(cli_ctx):
    clouds = []
    # load the config again as it may have changed
    config = get_config_parser()
    config.read(CLOUD_CONFIG_FILE)
    for section in config.sections():
        c = Cloud(section)
        for option in config.options(section):
            if option == 'profile':
                c.profile = config.get(section, option)
            if option.startswith('endpoint_'):
                setattr(c.endpoints, option.replace('endpoint_', ''), config.get(section, option))
            elif option.startswith('suffix_'):
                setattr(c.suffixes, option.replace('suffix_', ''), config.get(section, option))
        if c.profile is None:
            # If profile isn't set, use latest
            setattr(c, 'profile', 'latest')
        if c.profile not in API_PROFILES:
            raise CLIError('Profile {} does not exist or is not supported.'.format(c.profile))
        if not c.endpoints.has_endpoint_set('management') and \
                c.endpoints.has_endpoint_set('resource_manager'):
            # If management endpoint not set, use resource manager endpoint
            c.endpoints.management = c.endpoints.resource_manager
        clouds.append(c)
    active_cloud_name = get_active_cloud_name(cli_ctx)
    for c in clouds:
        if c.name == active_cloud_name:
            c.is_active = True
            break
    return clouds


def get_cloud(cli_ctx, cloud_name):
    cloud = _get_cloud(cli_ctx, cloud_name)
    if not cloud:
        raise CloudNotRegisteredException(cloud_name)
    return cloud


def get_active_cloud(cli_ctx):
    return get_cloud(cli_ctx, get_active_cloud_name(cli_ctx))


def get_cloud_subscription(cloud_name):
    config = get_config_parser()
    config.read(CLOUD_CONFIG_FILE)
    try:
        return config.get(cloud_name, 'subscription')
    except (configparser.NoOptionError, configparser.NoSectionError):
        return None


def set_cloud_subscription(cli_ctx, cloud_name, subscription):
    if not _get_cloud(cli_ctx, cloud_name):
        raise CloudNotRegisteredException(cloud_name)
    config = get_config_parser()
    config.read(CLOUD_CONFIG_FILE)
    if subscription:
        config.set(cloud_name, 'subscription', subscription)
    else:
        config.remove_option(cloud_name, 'subscription')
    if not os.path.isdir(GLOBAL_CONFIG_DIR):
        os.makedirs(GLOBAL_CONFIG_DIR)
    with open(CLOUD_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def _set_active_subscription(cloud_name):
    from azure.cli.core._profile import (Profile, _ENVIRONMENT_NAME, _SUBSCRIPTION_ID,
                                         _STATE, _SUBSCRIPTION_NAME)
    profile = Profile()
    subscription_to_use = get_cloud_subscription(cloud_name) or \
                          next((s[_SUBSCRIPTION_ID] for s in profile.load_cached_subscriptions()  # noqa
                                if s[_STATE] == 'Enabled'),
                               None)
    if subscription_to_use:
        try:
            profile.set_active_subscription(subscription_to_use)
            sub = profile.get_subscription(subscription_to_use)
            logger.warning("Active subscription switched to '%s (%s)'.",
                           sub[_SUBSCRIPTION_NAME], sub[_SUBSCRIPTION_ID])
        except CLIError as e:
            logger.warning(e)
            logger.warning("Unable to automatically switch the active subscription. "
                           "Use 'az account set'.")
    else:
        logger.warning("Use 'az login' to log in to this cloud.")
        logger.warning("Use 'az account set' to set the active subscription.")


def switch_active_cloud(cli_ctx, cloud_name):
    if cli_ctx.cloud.name == cloud_name:
        return
    if not _get_cloud(cli_ctx, cloud_name):
        raise CloudNotRegisteredException(cloud_name)
    _set_active_cloud(cli_ctx, cloud_name)
    logger.warning("Switched active cloud to '%s'.", cloud_name)
    _set_active_subscription(cloud_name)


def _config_add_cloud(config, cloud, overwrite=False):
    """ Add a cloud to a config object """
    try:
        config.add_section(cloud.name)
    except configparser.DuplicateSectionError:
        if not overwrite:
            raise CloudAlreadyRegisteredException(cloud.name)
    if cloud.profile:
        config.set(cloud.name, 'profile', cloud.profile)
    for k, v in cloud.endpoints.__dict__.items():
        if v is not None:
            config.set(cloud.name, 'endpoint_{}'.format(k), v)
    for k, v in cloud.suffixes.__dict__.items():
        if v is not None:
            config.set(cloud.name, 'suffix_{}'.format(k), v)


def _save_cloud(cloud, overwrite=False):
    config = get_config_parser()
    config.read(CLOUD_CONFIG_FILE)
    _config_add_cloud(config, cloud, overwrite=overwrite)
    if not os.path.isdir(GLOBAL_CONFIG_DIR):
        os.makedirs(GLOBAL_CONFIG_DIR)
    with open(CLOUD_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def add_cloud(cli_ctx, cloud):
    if _get_cloud(cli_ctx, cloud.name):
        raise CloudAlreadyRegisteredException(cloud.name)
    _save_cloud(cloud)


def update_cloud(cli_ctx, cloud):
    if not _get_cloud(cli_ctx, cloud.name):
        raise CloudNotRegisteredException(cloud.name)
    _save_cloud(cloud, overwrite=True)


def remove_cloud(cli_ctx, cloud_name):
    if not _get_cloud(cli_ctx, cloud_name):
        raise CloudNotRegisteredException(cloud_name)
    if cloud_name == cli_ctx.cloud.name:
        raise CannotUnregisterCloudException("The cloud '{}' cannot be unregistered "
                                             "as it's currently active.".format(cloud_name))
    is_known_cloud = next((x for x in KNOWN_CLOUDS if x.name == cloud_name), None)
    if is_known_cloud:
        raise CannotUnregisterCloudException("The cloud '{}' cannot be unregistered "
                                             "as it's not a custom cloud.".format(cloud_name))
    config = get_config_parser()
    config.read(CLOUD_CONFIG_FILE)
    config.remove_section(cloud_name)
    with open(CLOUD_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
