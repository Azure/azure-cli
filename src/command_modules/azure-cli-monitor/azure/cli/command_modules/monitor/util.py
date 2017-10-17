# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def get_resource_group_location(name):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType

    # pylint: disable=no-member
    return get_mgmt_service_client(ResourceType.MGMT_RESOURCE_RESOURCES).resource_groups.get(name).location
