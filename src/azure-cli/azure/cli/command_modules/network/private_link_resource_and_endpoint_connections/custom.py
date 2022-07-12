# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError

from .resource_providers import GeneralPrivateEndpointClient


TYPE_CLIENT_MAPPING = {
    # 'Microsoft.Keyvault/vaults': KeyVaultPrivateEndpointClient # vaults
}


def register_providers():
    _register_one_provider("Microsoft.Automation/automationAccounts", "2020-01-13-preview", True)
    _register_one_provider('Microsoft.Authorization/resourceManagementPrivateLinks', '2020-05-01', True)
    _register_one_provider('Microsoft.ApiManagement/service', '2021-08-01', True)
    _register_one_provider('Microsoft.AppConfiguration/configurationStores', '2020-06-01', True)
    _register_one_provider("Microsoft.Batch/batchAccounts", "2022-06-01", True)
    _register_one_provider("Microsoft.BotService/botServices", "2021-03-01", True)
    _register_one_provider("Microsoft.Cache/Redis", "2021-06-01", True)
    # "Microsoft.Cache/redisEnterprise", "2021-03-01", True
    _register_one_provider('Microsoft.CognitiveServices/accounts', '2022-03-01', True)
    _register_one_provider('Microsoft.Compute/diskAccesses', '2020-09-30', True)
    _register_one_provider('Microsoft.ContainerRegistry/registries', '2019-12-01-preview', True)
    _register_one_provider('Microsoft.DBforMySQL/servers', '2018-06-01', False, '2017-12-01-preview')
    _register_one_provider('Microsoft.DBforMariaDB/servers', '2018-06-01', False)
    _register_one_provider('Microsoft.DBforPostgreSQL/servers', '2018-06-01', False, '2017-12-01-preview')
    _register_one_provider('Microsoft.Devices/IotHubs', '2020-03-01', True)
    _register_one_provider('Microsoft.DocumentDB/databaseAccounts', '2019-08-01-preview', False, '2020-03-01')
    _register_one_provider('Microsoft.DigitalTwins/digitalTwinsInstances', '2020-12-01', True)
    _register_one_provider('Microsoft.EventGrid/topics', '2020-04-01-preview', True)
    _register_one_provider('Microsoft.EventGrid/domains', '2020-04-01-preview', True)
    _register_one_provider("Microsoft.EventHub/namespaces", "2021-06-01-preview", True)
    _register_one_provider("Microsoft.HDInsight/clusters", '2018-06-01-preview', True)
    _register_one_provider("Microsoft.HybridCompute/privateLinkScopes", '2021-05-20', True)
    _register_one_provider("Microsoft.HealthcareApis/services", "2020-03-30", True)
    _register_one_provider('microsoft.insights/privateLinkScopes', '2019-10-17-preview', True)
    _register_one_provider('Microsoft.KeyVault/managedHSMs', '2021-04-01-preview', True)
    _register_one_provider('Microsoft.Keyvault/vaults', '2019-09-01', False)
    _register_one_provider('Microsoft.MachineLearningServices/workspaces', '2021-01-01', True)
    _register_one_provider("Microsoft.Media/mediaservices", "2021-06-01", True)
    # _register_one_provider("Microsoft.Media/videoanalyzers", "2021-11-01-preview", True)
    # "Microsoft.Migrate/assessmentProjects", "2020-05-01-preview", False
    # "Microsoft.Migrate/migrateProjects", "2020-06-01-preview", False
    _register_one_provider('Microsoft.Network/applicationGateways', '2020-05-01', True)
    _register_one_provider('Microsoft.Network/privateLinkServices', '2021-05-01', True)
    # "Microsoft.OffAzure/masterSites", "2020-07-07", False
    _register_one_provider("Microsoft.Purview/accounts", "2021-07-01", True)
    _register_one_provider('Microsoft.PowerBI/privateLinkServicesForPowerBI', '2020-06-01', False)
    _register_one_provider('Microsoft.Search/searchServices', '2020-08-01', True)
    _register_one_provider("Microsoft.ServiceBus/namespaces", "2021-06-01-preview", True)
    _register_one_provider('Microsoft.SignalRService/signalr', '2020-05-01', False)
    _register_one_provider('Microsoft.Sql/servers', '2018-06-01-preview', True)
    _register_one_provider('Microsoft.Storage/storageAccounts', '2019-06-01', True)
    _register_one_provider("Microsoft.StorageSync/storageSyncServices", "2020-03-01", True)
    _register_one_provider("Microsoft.Synapse/workspaces", "2019-06-01-preview", True)
    _register_one_provider('Microsoft.Web/sites', '2019-08-01', False)
    _register_one_provider("Microsoft.Web/hostingEnvironments", "2020-10-01", True)
    _register_one_provider('Microsoft.SignalRService/WebPubSub', '2021-09-01-preview', False)
    _register_one_provider('Microsoft.DataFactory/factories', '2018-06-01', True)
    _register_one_provider('Microsoft.Databricks/workspaces', '2021-04-01-preview', True)
    _register_one_provider('Microsoft.RecoveryServices/vaults', '2021-07-01', True)
    _register_one_provider('Microsoft.Kusto/clusters', '2021-08-27', True)
    _register_one_provider("Microsoft.KubernetesConfiguration/privateLinkScopes", '2022-04-02-preview', True)


def _register_one_provider(provider, api_version, support_list_or_not, resource_get_api_version=None, support_connection_operation=True):  # pylint: disable=line-too-long
    """
    :param provider: namespace + type.
    :param api_version: API version for private link scenarios.
    :param support_list_or_not: support list rest call or not.
    :param resource_get_api_version: API version to get the service resource.
    """
    general_client_settings = {
        "api_version": api_version,
        "support_list_or_not": support_list_or_not,
        "resource_get_api_version": resource_get_api_version,
        "support_connection_operation": support_connection_operation
    }

    TYPE_CLIENT_MAPPING[provider] = general_client_settings


def _check_connection_operation_support(rp_mapping, resource_provider):
    if resource_provider in rp_mapping \
       and isinstance(rp_mapping[resource_provider], dict) \
       and not rp_mapping[resource_provider]['support_connection_operation']:
        raise CLIError("Resource provider {} currently does not support this operation".format(resource_provider))


def _get_client(rp_mapping, resource_provider):
    for key, value in rp_mapping.items():
        if str.lower(key) == str.lower(resource_provider):
            if isinstance(value, dict):
                return GeneralPrivateEndpointClient(key,
                                                    value['api_version'],
                                                    value['support_list_or_not'],
                                                    value['resource_get_api_version'])
            return value()
    raise CLIError("Resource type must be one of {}".format(", ".join(rp_mapping.keys())))


def list_private_link_resource(cmd, resource_group_name, name, resource_provider):
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)
    return client.list_private_link_resource(cmd, resource_group_name, name)


def approve_private_endpoint_connection(cmd, resource_group_name, resource_name, resource_provider,
                                        name, approval_description=None):
    _check_connection_operation_support(TYPE_CLIENT_MAPPING, resource_provider)
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)
    return client.approve_private_endpoint_connection(cmd, resource_group_name,
                                                      resource_name, name,
                                                      approval_description)


def reject_private_endpoint_connection(cmd, resource_group_name, resource_name, resource_provider,
                                       name, rejection_description=None):
    _check_connection_operation_support(TYPE_CLIENT_MAPPING, resource_provider)
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)
    return client.reject_private_endpoint_connection(cmd, resource_group_name,
                                                     resource_name, name,
                                                     rejection_description)


def remove_private_endpoint_connection(cmd, resource_group_name, resource_name, resource_provider, name):
    _check_connection_operation_support(TYPE_CLIENT_MAPPING, resource_provider)
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)
    return client.remove_private_endpoint_connection(cmd, resource_group_name, resource_name, name)


def show_private_endpoint_connection(cmd, resource_group_name, resource_name, resource_provider, name):
    _check_connection_operation_support(TYPE_CLIENT_MAPPING, resource_provider)
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)
    return client.show_private_endpoint_connection(cmd, resource_group_name, resource_name, name)


def list_private_endpoint_connection(cmd, resource_group_name, name, resource_provider):
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)
    return client.list_private_endpoint_connection(cmd, resource_group_name, name)
