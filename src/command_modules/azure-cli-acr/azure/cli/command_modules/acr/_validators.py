#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core._util import CLIError

from ._factory import get_arm_service_client

import azure.cli.core._logging as _logging
logger = _logging.get_az_logger(__name__)

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