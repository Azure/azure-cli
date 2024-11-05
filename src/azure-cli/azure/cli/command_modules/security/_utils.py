# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import (
    CLIInternalError
)


def get_resource_group(cmd, resource_group_name):
    '''Get resource group info
    :param cmd: The cmd context
    :param resource_group_name: The resource group to be fetched
    '''
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    try:
        resource_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
        resource_group = resource_client.resource_groups.get(resource_group_name)
    except Exception as ex:  # pylint: disable=broad-except
        raise CLIInternalError('Resource group fetch execution failed, error message is: {}'.format(str(ex)))
    return resource_group
