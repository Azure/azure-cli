# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def iot_hub_service_factory(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.iothub.iot_hub_client import IotHubClient
    return get_mgmt_service_client(cli_ctx, IotHubClient)


def resource_service_factory(cli_ctx, **_):
    from azure.mgmt.resource import ResourceManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceManagementClient)


def iot_service_provisioning_factory(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.iothubprovisioningservices.iot_dps_client import IotDpsClient
    return get_mgmt_service_client(cli_ctx, IotDpsClient)
