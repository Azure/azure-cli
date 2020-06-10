# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .resource_providers import GeneralPrivateEndpointClient
from knack.util import CLIError

TYPE_CLIENT_MAPPING = {
    # 'Microsoft.Keyvault/vaults': KeyVaultPrivateEndpointClient # vaults
}


def register_providers():
    _register_one_provider('Microsoft.Storage/storageAccounts', '2019-06-01', False)
    _register_one_provider('Microsoft.Keyvault/vaults', '2019-09-01', False)
    _register_one_provider('Microsoft.ContainerRegistry/registries', '2019-12-01-preview', True)
    _register_one_provider('microsoft.insights/privateLinkScopes', '2019-10-17-preview', True)
    _register_one_provider('Microsoft.DBforMySQL/servers', '2018-06-01', False, '2017-12-01-preview')
    _register_one_provider('Microsoft.DBforMariaDB/servers', '2018-06-01', False)
    _register_one_provider('Microsoft.DBforPostgreSQL/servers', '2018-06-01', False, '2017-12-01-preview')
    _register_one_provider('Microsoft.DocumentDB/databaseAccounts', '2019-08-01-preview', False, '2020-03-01')
    _register_one_provider('Microsoft.Devices/IotHubs', '2020-03-01', True)
    _register_one_provider('Microsoft.EventGrid/topics', '2020-04-01-preview', True)
    _register_one_provider('Microsoft.EventGrid/domains', '2020-04-01-preview', True)


def _register_one_provider(provider, api_version, support_list_or_not, resource_get_api_version=None):
    """
    :param provider: namespace + type.
    :param api_version: API version for private link scenarios.
    :param support_list_or_not: support list rest call or not.
    :param resource_get_api_version: API version to get the service resource.
    """
    general_client_settings = {
        "api_version": api_version,
        "support_list_or_not": support_list_or_not,
        "resource_get_api_version": resource_get_api_version
    }

    TYPE_CLIENT_MAPPING[provider] = general_client_settings


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
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)
    return client.approve_private_endpoint_connection(cmd, resource_group_name,
                                                      resource_name, name,
                                                      approval_description)


def reject_private_endpoint_connection(cmd, resource_group_name, resource_name, resource_provider,
                                       name, rejection_description=None):
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)
    return client.reject_private_endpoint_connection(cmd, resource_group_name,
                                                     resource_name, name,
                                                     rejection_description)


def remove_private_endpoint_connection(cmd, resource_group_name, resource_name, resource_provider, name):
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)
    return client.remove_private_endpoint_connection(cmd, resource_group_name, resource_name, name)


def show_private_endpoint_connection(cmd, resource_group_name, resource_name, resource_provider, name):
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)
    return client.show_private_endpoint_connection(cmd, resource_group_name, resource_name, name)


def list_private_endpoint_connection(cmd, resource_group_name, name, resource_provider):
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)
    return client.list_private_endpoint_connection(cmd, resource_group_name, name)
