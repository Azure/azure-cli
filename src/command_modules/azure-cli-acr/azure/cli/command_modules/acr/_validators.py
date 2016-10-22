#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import re
import uuid

from azure.cli.command_modules.acr.mgmt_acr.models import RegistryNameCheckRequest

from azure.cli.core._util import CLIError
from azure.cli.command_modules.storage._factory import storage_client_factory

from ._constants import RESOURCE_TYPE
from ._factory import (
    get_acr_service_client,
    get_arm_service_client
)
from ._arm_utils import arm_get_storage_account_by_name

import azure.cli.core._logging as _logging
logger = _logging.get_az_logger(__name__)

def validate_registry_name(namespace):
    if namespace.registry_name:
        registry_name = namespace.registry_name
        if len(registry_name) < 5 or len(registry_name) > 60:
            raise CLIError('The registry name must be between 5 and 60 characters.')

        p = re.compile('^([A-Za-z0-9]+)$')

        if not p.match(registry_name):
            raise CLIError('The registry name can contain only letters and numbers.')

def validate_registry_name_create(namespace):
    if namespace.registry_name:
        client = get_acr_service_client()

        result = client.operation.check_name_availability(
            RegistryNameCheckRequest(
                namespace.registry_name,
                RESOURCE_TYPE
            )
        )

        if not result.name_available: #pylint: disable=no-member
            raise CLIError(result.message) #pylint: disable=no-member

def validate_storage_account_name(namespace):
    client = storage_client_factory().storage_accounts

    if namespace.storage_account_name:
        storage_account_name = namespace.storage_account_name
        if arm_get_storage_account_by_name(storage_account_name) is None:
            logger.warning('Command to create a storage account:')
            logger.warning(
                '  az storage account create ' +\
                '-n <name> -g <resource-group> -l <location> --sku Standard_LRS')
            logger.warning(
                'The container registry must be at the same location as the storage account.')
            raise CLIError(
                'The storage account {} does not exist in the current subscription.'\
                .format(storage_account_name))
    else:
        while True:
            storage_account_name = str(uuid.uuid4()).replace('-', '')[:24]
            if client.check_name_availability(storage_account_name).name_available is True: #pylint: disable=no-member
                namespace.storage_account_name = storage_account_name
                logger.warning(
                    'New storage account with name %s will be created and used.',
                    storage_account_name)
                return

def validate_resource_group_name(namespace):
    if namespace.resource_group_name:
        client = get_arm_service_client()
        resource_group_name = namespace.resource_group_name

        if not client.resource_groups.check_existence(resource_group_name):
            logger.warning('Command to create a resource group:')
            logger.warning('  az resource group create -n <name> -l <location>')
            raise CLIError(
                'The resource group {} does not exist in the current subscription.'\
                .format(resource_group_name))
