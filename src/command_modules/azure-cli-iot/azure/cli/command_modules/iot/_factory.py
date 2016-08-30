#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
#pylint: disable=unused-argument

from azure.cli.commands.client_factory import get_mgmt_service_client
from azure.cli.command_modules.iot.mgmt_iot_hub.lib.iot_hub_client import IotHubClient
from azure.mgmt.resource.resources import ResourceManagementClient


def iot_hub_service_factory(kwargs):
    return get_mgmt_service_client(IotHubClient).iot_hub_resource


def resource_service_factory(**kwargs):
    return get_mgmt_service_client(ResourceManagementClient)
