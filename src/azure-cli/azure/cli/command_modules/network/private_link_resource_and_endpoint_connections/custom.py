# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .resource_providers.keyvault_provider import KeyVaultPrivateEndpointClient
from knack.util import CLIError

TYPE_CLIENT_MAPPING = {
    'microsoft.keyvault/vaults': KeyVaultPrivateEndpointClient # vaults
}


def _get_client(rp_mapping, resource_provider):

    for key, value in rp_mapping.items():
        if str.lower(key) == str.lower(resource_provider):
            return value
    raise CLIError("Resource type must be one of {}".format(", ".join(rp_mapping.keys())))


def list_private_link_resource(cmd, resource_group_name, name, resource_provider):
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)()
    return client.list_private_link_resource(cmd, resource_group_name, name)


def approve_private_endpoint_connection(cmd, resource_group_name, service_name, resource_provider,
                                        name, approval_description=None):
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)()
    return client.approve_private_endpoint_connection(cmd, resource_group_name, service_name, name, approval_description)


def reject_private_endpoint_connection(cmd, resource_group_name, service_name, resource_provider,
                                       name, rejection_description=None):
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)()
    return client.reject_private_endpoint_connection(cmd, resource_group_name, service_name, name, rejection_description)


def remove_private_endpoint_connection(cmd, resource_group_name, service_name, resource_provider, name):
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)()
    return client.remove_private_endpoint_connection(cmd, resource_group_name, service_name, name)


def show_private_endpoint_connection(cmd, resource_group_name, service_name, resource_provider, name):
    client = _get_client(TYPE_CLIENT_MAPPING, resource_provider)()
    return client.show_private_endpoint_connection(cmd, resource_group_name, service_name, name)
