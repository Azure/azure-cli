# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import os
import json
from pprint import pformat
import configparser

from azure.cli.core.profiles import API_PROFILES
from azure.cli.core._config import GLOBAL_CONFIG_DIR
from azure.cli.core.util import urlretrieve

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)

CLOUD_CONFIG_FILE = os.path.join(GLOBAL_CONFIG_DIR, 'clouds.config')

# Add names of clouds that don't allow telemetry data collection here such as JEDI.
CLOUDS_FORBIDDING_TELEMETRY = []


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


class CloudEndpoints:  # pylint: disable=too-few-public-methods,too-many-instance-attributes

    def __init__(self,
                 management=None,
                 resource_manager=None,
                 sql_management=None,
                 batch_resource_id=None,
                 gallery=None,
                 active_directory=None,
                 active_directory_resource_id=None,
                 active_directory_graph_resource_id=None,
                 microsoft_graph_resource_id=None,
                 active_directory_data_lake_resource_id=None,
                 vm_image_alias_doc=None,
                 media_resource_id=None,
                 ossrdbms_resource_id=None,
                 log_analytics_resource_id=None,
                 app_insights_resource_id=None,
                 app_insights_telemetry_channel_resource_id=None,
                 synapse_analytics_resource_id=None):
        # Attribute names are significant. They are used when storing/retrieving clouds from config
        self.management = management
        self.resource_manager = resource_manager
        self.sql_management = sql_management
        self.batch_resource_id = batch_resource_id
        self.gallery = gallery
        self.active_directory = active_directory
        self.active_directory_resource_id = active_directory_resource_id
        self.active_directory_graph_resource_id = active_directory_graph_resource_id
        self.microsoft_graph_resource_id = microsoft_graph_resource_id
        self.active_directory_data_lake_resource_id = active_directory_data_lake_resource_id
        self.vm_image_alias_doc = vm_image_alias_doc
        self.media_resource_id = media_resource_id
        self.ossrdbms_resource_id = ossrdbms_resource_id
        self.log_analytics_resource_id = log_analytics_resource_id
        self.app_insights_resource_id = app_insights_resource_id
        self.app_insights_telemetry_channel_resource_id = app_insights_telemetry_channel_resource_id
        self.synapse_analytics_resource_id = synapse_analytics_resource_id

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
                                               "is not set but is used.\n"
                                               "{} may be corrupt or invalid.\nResolve the error or delete this file "
                                               "and try again.".format(name, CLOUD_CONFIG_FILE))
        return val


class CloudSuffixes:  # pylint: disable=too-few-public-methods,too-many-instance-attributes

    def __init__(self,
                 storage_endpoint=None,
                 storage_sync_endpoint=None,
                 keyvault_dns=None,
                 sql_server_hostname=None,
                 azure_datalake_store_file_system_endpoint=None,
                 azure_datalake_analytics_catalog_and_job_endpoint=None,
                 acr_login_server_endpoint=None,
                 mysql_server_endpoint=None,
                 postgresql_server_endpoint=None,
                 mariadb_server_endpoint=None,
                 synapse_analytics_endpoint=None):
        # Attribute names are significant. They are used when storing/retrieving clouds from config
        self.storage_endpoint = storage_endpoint
        self.storage_sync_endpoint = storage_sync_endpoint
        self.keyvault_dns = keyvault_dns
        self.sql_server_hostname = sql_server_hostname
        self.mysql_server_endpoint = mysql_server_endpoint
        self.postgresql_server_endpoint = postgresql_server_endpoint
        self.mariadb_server_endpoint = mariadb_server_endpoint
        self.azure_datalake_store_file_system_endpoint = azure_datalake_store_file_system_endpoint
        self.azure_datalake_analytics_catalog_and_job_endpoint = azure_datalake_analytics_catalog_and_job_endpoint
        self.acr_login_server_endpoint = acr_login_server_endpoint
        self.synapse_analytics_endpoint = synapse_analytics_endpoint

    def __getattribute__(self, name):
        val = object.__getattribute__(self, name)
        if val is None:
            raise CloudSuffixNotSetException("The suffix '{}' for this cloud "
                                             "is not set but is used.\n"
                                             "{} may be corrupt or invalid.\nResolve the error or delete this file "
                                             "and try again.".format(name, CLOUD_CONFIG_FILE))
        return val


def _get_ossrdbms_resource_id(cloud_name):
    ossrdbms_mapper = {
        'AzureCloud': 'https://ossrdbms-aad.database.windows.net',
        'AzureChinaCloud': 'https://ossrdbms-aad.database.chinacloudapi.cn',
        'AzureUSGovernment': 'https://ossrdbms-aad.database.usgovcloudapi.net',
        'AzureGermanCloud': 'https://ossrdbms-aad.database.cloudapi.de'
    }
    return ossrdbms_mapper.get(cloud_name, None)


def _get_microsoft_graph_resource_id(cloud_name):
    graph_endpoint_mapper = {
        'AzureCloud': 'https://graph.microsoft.com/',
        'AzureChinaCloud': 'https://microsoftgraph.chinacloudapi.cn/',
        'AzureUSGovernment': 'https://graph.microsoft.us/',
        'AzureGermanCloud': 'https://graph.microsoft.de/'
    }
    return graph_endpoint_mapper.get(cloud_name, None)


def _get_storage_sync_endpoint(cloud_name):
    storage_sync_endpoint_mapper = {
        'AzureCloud': 'afs.azure.net',
        'AzureUSGovernment': 'afs.azure.us',
    }
    return storage_sync_endpoint_mapper.get(cloud_name, None)


def _get_synapse_analytics_endpoint(cloud_name):
    synapse_analytics_endpoint_mapper = {
        'AzureCloud': 'dev.azuresynapse.net',
        'AzureChinaCloud': 'dev.azuresynapse.azure.cn'
    }
    return synapse_analytics_endpoint_mapper.get(cloud_name, None)


def _get_database_server_endpoint(sql_server_hostname, cloud_name):
    def _concat_db_server_endpoint(db_prefix):
        if cloud_name == 'AzureCloud':
            return db_prefix + '.database.azure.com'
        if not sql_server_hostname:
            return None
        return db_prefix + sql_server_hostname
    return _concat_db_server_endpoint


def _get_app_insights_telemetry_channel_resource_id(cloud_name):
    app_insights_telemetry_channel_resource_id_mapper = {
        'AzureCloud': 'https://dc.applicationinsights.azure.com/v2/track',
        'AzureChinaCloud': 'https://dc.applicationinsights.azure.cn/v2/track',
        'AzureUSGovernment': 'https://dc.applicationinsights.us/v2/track'
    }
    return app_insights_telemetry_channel_resource_id_mapper.get(cloud_name, None)


def _get_log_analytics_resource_id(cloud_name):
    log_analytics_resource_id_mapper = {
        'AzureCloud': 'https://api.loganalytics.io',
        'AzureChinaCloud': 'https://api.loganalytics.azure.cn',
        'AzureUSGovernment': 'https://api.loganalytics.us'
    }
    return log_analytics_resource_id_mapper.get(cloud_name, None)


def _get_app_insights_resource_id(cloud_name):
    app_insights_resource_id_mapper = {
        'AzureCloud': 'https://api.applicationinsights.io',
        'AzureChinaCloud': 'https://api.applicationinsights.azure.cn',
        'AzureUSGovernment': 'https://api.applicationinsights.us'
    }
    return app_insights_resource_id_mapper.get(cloud_name, None)


def _get_synapse_analytics_resource_id(cloud_name):
    synapse_analytics_resource_id_mapper = {
        'AzureCloud': 'https://dev.azuresynapse.net',
        'AzureChinaCloud': 'https://dev.azuresynapse.net'
    }
    return synapse_analytics_resource_id_mapper.get(cloud_name, None)


def _convert_arm_to_cli(arm_cloud_metadata_dict):
    cli_cloud_metadata_dict = {}
    for cloud in arm_cloud_metadata_dict:
        cli_cloud_metadata_dict[cloud['name']] = _arm_to_cli_mapper(cloud)
    if 'AzureCloud' in cli_cloud_metadata_dict:
        cli_cloud_metadata_dict['AzureCloud'].endpoints.active_directory = 'https://login.microsoftonline.com'  # change once active_directory is fixed in ARM for the public cloud
    return cli_cloud_metadata_dict


def _add_starting_dot(suffix):
    return suffix if not suffix or suffix.startswith('.') else '.' + suffix


def _get_arm_endpoint(arm_dict, is_suffix=False):
    def _get_processed_arm_endpoint(name, add_dot=False, fallback_value=None):
        if is_suffix:
            return (_add_starting_dot(arm_dict['suffixes'][name]) if add_dot else arm_dict['suffixes'][name]) if name in arm_dict['suffixes'] else fallback_value
        return arm_dict[name] if name in arm_dict else fallback_value
    return _get_processed_arm_endpoint


def _arm_to_cli_mapper(arm_dict):
    get_endpoint = _get_arm_endpoint(arm_dict)
    get_suffix = _get_arm_endpoint(arm_dict, is_suffix=True)

    sql_server_hostname = get_suffix('sqlServerHostname', add_dot=True)
    get_db_server_endpoint = _get_database_server_endpoint(sql_server_hostname, arm_dict['name'])

    return Cloud(
        arm_dict['name'],
        endpoints=CloudEndpoints(
            management=arm_dict['authentication']['audiences'][0],
            resource_manager=arm_dict['resourceManager'],
            sql_management=arm_dict['sqlManagement'],
            batch_resource_id=arm_dict['batch'],
            gallery=arm_dict['gallery'],
            active_directory=arm_dict['authentication']['loginEndpoint'],
            active_directory_resource_id=arm_dict['authentication']['audiences'][0],
            active_directory_graph_resource_id=arm_dict['graphAudience'],
            microsoft_graph_resource_id=_get_microsoft_graph_resource_id(arm_dict['name']),  # change once microsoft_graph_resource_id is fixed in ARM
            vm_image_alias_doc=arm_dict['vmImageAliasDoc'],
            media_resource_id=arm_dict['media'],
            ossrdbms_resource_id=_get_ossrdbms_resource_id(arm_dict['name']),  # change once ossrdbms_resource_id is available via ARM
            active_directory_data_lake_resource_id=arm_dict['activeDirectoryDataLake'] if 'activeDirectoryDataLake' in arm_dict else None,
            app_insights_resource_id=get_endpoint('appInsightsResourceId', fallback_value=_get_app_insights_resource_id(arm_dict['name'])),
            log_analytics_resource_id=get_endpoint('logAnalyticsResourceId', fallback_value=_get_log_analytics_resource_id(arm_dict['name'])),
            synapse_analytics_resource_id=get_endpoint('synapseAnalyticsResourceId', fallback_value=_get_synapse_analytics_resource_id(arm_dict['name'])),
            app_insights_telemetry_channel_resource_id=get_endpoint('appInsightsTelemetryChannelResourceId', fallback_value=_get_app_insights_telemetry_channel_resource_id(arm_dict['name']))),
        suffixes=CloudSuffixes(
            storage_endpoint=get_suffix('storage'),
            storage_sync_endpoint=get_suffix('storageSyncEndpointSuffix', fallback_value=_get_storage_sync_endpoint(arm_dict['name'])),
            keyvault_dns=get_suffix('keyVaultDns', add_dot=True),
            sql_server_hostname=sql_server_hostname,
            mysql_server_endpoint=get_suffix('mysqlServerEndpoint', add_dot=True, fallback_value=get_db_server_endpoint('.mysql')),
            postgresql_server_endpoint=get_suffix('postgresqlServerEndpoint', add_dot=True, fallback_value=get_db_server_endpoint('.postgres')),
            mariadb_server_endpoint=get_suffix('mariadbServerEndpoint', add_dot=True, fallback_value=get_db_server_endpoint('.mariadb')),
            azure_datalake_store_file_system_endpoint=get_suffix('azureDataLakeStoreFileSystem'),
            azure_datalake_analytics_catalog_and_job_endpoint=get_suffix('azureDataLakeAnalyticsCatalogAndJob'),
            synapse_analytics_endpoint=get_suffix('synapseAnalytics', add_dot=True, fallback_value=_get_synapse_analytics_endpoint(arm_dict['name'])),
            acr_login_server_endpoint=get_suffix('acrLoginServer', add_dot=True)))


class Cloud:  # pylint: disable=too-few-public-methods
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
        microsoft_graph_resource_id='https://graph.microsoft.com/',
        active_directory_data_lake_resource_id='https://datalake.azure.net/',
        vm_image_alias_doc='https://raw.githubusercontent.com/Azure/azure-rest-api-specs/master/arm-compute/quickstart-templates/aliases.json',
        media_resource_id='https://rest.media.azure.net',
        ossrdbms_resource_id='https://ossrdbms-aad.database.windows.net',
        app_insights_resource_id='https://api.applicationinsights.io',
        log_analytics_resource_id='https://api.loganalytics.io',
        app_insights_telemetry_channel_resource_id='https://dc.applicationinsights.azure.com/v2/track',
        synapse_analytics_resource_id='https://dev.azuresynapse.net'),
    suffixes=CloudSuffixes(
        storage_endpoint='core.windows.net',
        storage_sync_endpoint='afs.azure.net',
        keyvault_dns='.vault.azure.net',
        sql_server_hostname='.database.windows.net',
        mysql_server_endpoint='.mysql.database.azure.com',
        postgresql_server_endpoint='.postgres.database.azure.com',
        mariadb_server_endpoint='.mariadb.database.azure.com',
        azure_datalake_store_file_system_endpoint='azuredatalakestore.net',
        azure_datalake_analytics_catalog_and_job_endpoint='azuredatalakeanalytics.net',
        acr_login_server_endpoint='.azurecr.io',
        synapse_analytics_endpoint='.dev.azuresynapse.net'))

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
        microsoft_graph_resource_id='https://microsoftgraph.chinacloudapi.cn',
        vm_image_alias_doc='https://raw.githubusercontent.com/Azure/azure-rest-api-specs/master/arm-compute/quickstart-templates/aliases.json',
        media_resource_id='https://rest.media.chinacloudapi.cn',
        ossrdbms_resource_id='https://ossrdbms-aad.database.chinacloudapi.cn',
        app_insights_resource_id='https://api.applicationinsights.azure.cn',
        log_analytics_resource_id='https://api.loganalytics.azure.cn',
        app_insights_telemetry_channel_resource_id='https://dc.applicationinsights.azure.cn/v2/track',
        synapse_analytics_resource_id='https://dev.azuresynapse.net'),
    suffixes=CloudSuffixes(
        storage_endpoint='core.chinacloudapi.cn',
        keyvault_dns='.vault.azure.cn',
        sql_server_hostname='.database.chinacloudapi.cn',
        mysql_server_endpoint='.mysql.database.chinacloudapi.cn',
        postgresql_server_endpoint='.postgres.database.chinacloudapi.cn',
        mariadb_server_endpoint='.mariadb.database.chinacloudapi.cn',
        acr_login_server_endpoint='.azurecr.cn',
        synapse_analytics_endpoint='.dev.azuresynapse.azure.cn'))

AZURE_US_GOV_CLOUD = Cloud(
    'AzureUSGovernment',
    endpoints=CloudEndpoints(
        management='https://management.core.usgovcloudapi.net/',
        resource_manager='https://management.usgovcloudapi.net/',
        sql_management='https://management.core.usgovcloudapi.net:8443/',
        batch_resource_id='https://batch.core.usgovcloudapi.net/',
        gallery='https://gallery.usgovcloudapi.net/',
        active_directory='https://login.microsoftonline.us',
        active_directory_resource_id='https://management.core.usgovcloudapi.net/',
        active_directory_graph_resource_id='https://graph.windows.net/',
        microsoft_graph_resource_id='https://graph.microsoft.us/',
        vm_image_alias_doc='https://raw.githubusercontent.com/Azure/azure-rest-api-specs/master/arm-compute/quickstart-templates/aliases.json',
        media_resource_id='https://rest.media.usgovcloudapi.net',
        ossrdbms_resource_id='https://ossrdbms-aad.database.usgovcloudapi.net',
        app_insights_resource_id='https://api.applicationinsights.us',
        log_analytics_resource_id='https://api.loganalytics.us',
        app_insights_telemetry_channel_resource_id='https://dc.applicationinsights.us/v2/track'),
    suffixes=CloudSuffixes(
        storage_endpoint='core.usgovcloudapi.net',
        storage_sync_endpoint='afs.azure.us',
        keyvault_dns='.vault.usgovcloudapi.net',
        sql_server_hostname='.database.usgovcloudapi.net',
        mysql_server_endpoint='.mysql.database.usgovcloudapi.net',
        postgresql_server_endpoint='.postgres.database.usgovcloudapi.net',
        mariadb_server_endpoint='.mariadb.database.usgovcloudapi.net',
        acr_login_server_endpoint='.azurecr.us'))

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
        microsoft_graph_resource_id='https://graph.microsoft.de',
        vm_image_alias_doc='https://raw.githubusercontent.com/Azure/azure-rest-api-specs/master/arm-compute/quickstart-templates/aliases.json',
        media_resource_id='https://rest.media.cloudapi.de',
        ossrdbms_resource_id='https://ossrdbms-aad.database.cloudapi.de'),
    suffixes=CloudSuffixes(
        storage_endpoint='core.cloudapi.de',
        keyvault_dns='.vault.microsoftazure.de',
        sql_server_hostname='.database.cloudapi.de',
        mysql_server_endpoint='.mysql.database.cloudapi.de',
        postgresql_server_endpoint='.postgres.database.cloudapi.de',
        mariadb_server_endpoint='.mariadb.database.cloudapi.de'))

KNOWN_CLOUDS = [AZURE_PUBLIC_CLOUD, AZURE_CHINA_CLOUD, AZURE_US_GOV_CLOUD, AZURE_GERMAN_CLOUD]

if 'ARM_CLOUD_METADATA_URL' in os.environ:
    try:
        arm_cloud_dict = json.loads(urlretrieve(os.getenv('ARM_CLOUD_METADATA_URL')))
        cli_cloud_dict = _convert_arm_to_cli(arm_cloud_dict)
        if 'AzureCloud' in cli_cloud_dict:
            cli_cloud_dict['AzureCloud'].endpoints.active_directory = 'https://login.microsoftonline.com'  # change once active_directory is fixed in ARM for the public cloud
        KNOWN_CLOUDS = list(cli_cloud_dict.values())
    except Exception as ex:  # pylint: disable=broad-except
        logger.warning('Failed to load cloud metadata from the url specified by ARM_CLOUD_METADATA_URL')
        raise ex


def _set_active_cloud(cli_ctx, cloud_name):
    cli_ctx.config.set_value('cloud', 'name', cloud_name)
    cli_ctx.cloud = get_cloud(cli_ctx, cloud_name)


def get_active_cloud_name(cli_ctx):
    try:
        return cli_ctx.config.get('cloud', 'name')
    except (configparser.NoOptionError, configparser.NoSectionError):
        _set_active_cloud(cli_ctx, AZURE_PUBLIC_CLOUD.name)
        return AZURE_PUBLIC_CLOUD.name


def _get_cloud(cli_ctx, cloud_name):
    return next((x for x in get_clouds(cli_ctx) if x.name == cloud_name), None)


def cloud_is_registered(cli_ctx, cloud_name):
    return bool(_get_cloud(cli_ctx, cloud_name))


def get_custom_clouds(cli_ctx):
    known_cloud_names = [c.name for c in KNOWN_CLOUDS]
    return [c for c in get_clouds(cli_ctx) if c.name not in known_cloud_names]


def _get_cloud_name(cli_ctx, cloud_name):
    return next((x.name for x in get_clouds(cli_ctx) if x.name.lower() == cloud_name.lower()), cloud_name)


def get_clouds(cli_ctx):
    clouds = []
    config = configparser.ConfigParser()
    # Start off with known clouds and apply config file on top of current config
    for c in KNOWN_CLOUDS:
        _config_add_cloud(config, c)
    try:
        config.read(CLOUD_CONFIG_FILE)
    except configparser.MissingSectionHeaderError:
        os.remove(CLOUD_CONFIG_FILE)
        logger.warning("'%s' is in bad format and has been removed.", CLOUD_CONFIG_FILE)
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


def get_active_cloud(cli_ctx=None):
    if not cli_ctx:
        from azure.cli.core import get_default_cli
        cli_ctx = get_default_cli()
    try:
        return get_cloud(cli_ctx, get_active_cloud_name(cli_ctx))
    except CloudNotRegisteredException as err:
        logger.warning(err)
        logger.warning("Resetting active cloud to'%s'.", AZURE_PUBLIC_CLOUD.name)
        _set_active_cloud(cli_ctx, AZURE_PUBLIC_CLOUD.name)
        return get_cloud(cli_ctx, AZURE_PUBLIC_CLOUD.name)


def get_cloud_subscription(cloud_name):
    config = configparser.ConfigParser()
    config.read(CLOUD_CONFIG_FILE)
    try:
        return config.get(cloud_name, 'subscription')
    except (configparser.NoOptionError, configparser.NoSectionError):
        return None


def set_cloud_subscription(cli_ctx, cloud_name, subscription):
    if not _get_cloud(cli_ctx, cloud_name):
        raise CloudNotRegisteredException(cloud_name)
    config = configparser.ConfigParser()
    config.read(CLOUD_CONFIG_FILE)
    if subscription:
        try:
            config.add_section(cloud_name)
        except configparser.DuplicateSectionError:
            pass
        config.set(cloud_name, 'subscription', subscription)
    else:
        try:
            config.remove_option(cloud_name, 'subscription')
        except configparser.NoSectionError:
            pass
    if not os.path.isdir(GLOBAL_CONFIG_DIR):
        os.makedirs(GLOBAL_CONFIG_DIR)
    with open(CLOUD_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def _set_active_subscription(cli_ctx, cloud_name):
    from azure.cli.core._profile import (Profile, _ENVIRONMENT_NAME, _SUBSCRIPTION_ID,
                                         _STATE, _SUBSCRIPTION_NAME)
    profile = Profile(cli_ctx=cli_ctx)
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
    _set_active_subscription(cli_ctx, cloud_name)


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
    config = configparser.ConfigParser()
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
    config = configparser.ConfigParser()
    config.read(CLOUD_CONFIG_FILE)
    config.remove_section(cloud_name)
    with open(CLOUD_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def cloud_forbid_telemetry(cli_ctx):
    return get_active_cloud_name(cli_ctx) in CLOUDS_FORBIDDING_TELEMETRY
