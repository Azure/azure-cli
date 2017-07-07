# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client


def get_arm_service_client():
    """Returns the client for managing ARM resources. """
    from azure.mgmt.resource import ResourceManagementClient
    return get_mgmt_service_client(ResourceManagementClient)


def get_storage_service_client():
    """Returns the client for managing storage accounts. """
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(ResourceType.MGMT_STORAGE)


def get_acr_service_client(api_version=None):
    """Returns the client for managing container registries. """
    from azure.mgmt.containerregistry import ContainerRegistryManagementClient
    return get_mgmt_service_client(ContainerRegistryManagementClient, api_version=api_version)
