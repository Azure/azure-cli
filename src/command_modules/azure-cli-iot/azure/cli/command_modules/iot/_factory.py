# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def iot_hub_service_factory(_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.iothub.iot_hub_client import IotHubClient
    return get_mgmt_service_client(IotHubClient).iot_hub_resource


def resource_service_factory(**_):
    from azure.mgmt.resource import ResourceManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(ResourceManagementClient)
