# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core._config import az_config
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.containerregistry import ContainerRegistryManagementClient

from azure.cli.core.commands.client_factory import get_mgmt_service_client

import azure.cli.core._logging as _logging
logger = _logging.get_az_logger(__name__)

def get_arm_service_client():
    '''Returns the client for managing ARM resources.
    '''
    return get_mgmt_service_client(ResourceManagementClient)

def get_storage_service_client():
    '''Returns the client for managing storage accounts.
    '''
    return get_mgmt_service_client(StorageManagementClient)

def get_acr_service_client():
    '''Returns the client for managing container registries.
    '''
    customized_api_version = get_acr_api_version()
    if customized_api_version:
        return get_mgmt_service_client(ContainerRegistryManagementClient,
                                       api_version=customized_api_version)
    else:
        return get_mgmt_service_client(ContainerRegistryManagementClient)

def get_acr_api_version():
    '''Returns the api version for container registry
    '''
    customized_api_version = az_config.get('acr', 'apiversion', None)
    if customized_api_version:
        logger.warning('Customized api-version is used: %s', customized_api_version)
    return customized_api_version
