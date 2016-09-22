#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
# pylint: disable=no-self-use,too-many-arguments,no-member,line-too-long

from __future__ import print_function
import azure.cli.core._logging as _logging
from azure.cli.core._util import CLIError
from azure.mgmt.iothub.models.iot_hub_client_enums import IotHubSku
from azure.mgmt.iothub.models.iot_hub_description import IotHubDescription
from azure.mgmt.iothub.models.iot_hub_sku_info import IotHubSkuInfo
from azure.cli.command_modules.iot.mgmt_iot_hub_device.lib.iot_hub_device_client import \
    IotHubDeviceClient
from azure.cli.command_modules.iot.mgmt_iot_hub_device.lib.models.create_device_request import \
    CreateDeviceRequest
from azure.cli.command_modules.iot.sas_token_auth import SasTokenAuthentication
from ._factory import resource_service_factory

logger = _logging.get_az_logger(__name__)


# CUSTOM METHODS


def iot_hub_create(client, name, resource_group_name,
                   location=None, sku=IotHubSku.f1.value, unit=1):
    name_availability = client.check_name_availability(name)
    logger.info('name availability info: %s', name_availability)
    if name_availability is not None and not name_availability.name_available:
        raise CLIError(name_availability.message)

    if location is None:
        logger.info('Location is none. Use location of resource group as default.')
        resource_group_client = resource_service_factory().resource_groups
        group_info = resource_group_client.get(resource_group_name)
        location = group_info.location
        logger.info('Location to use: %s', location)

    iot_hub_description = IotHubDescription(location=location,
                                            sku=IotHubSkuInfo(name=sku, capacity=unit))
    result = client.create_or_update(resource_group_name=resource_group_name, resource_name=name,
                                     iot_hub_description=iot_hub_description)
    return result


def iot_hub_get_connection_string(client, name, resource_group_name, policy_name='iothubowner'):
    access_policies = client.list_keys(resource_group_name, name).next()
    if access_policies is None:
        raise CLIError('No policy found from IoT Hub: {}.'.format(name))
    logger.info('Shared Access Polices: %s', str(access_policies))
    try:
        access_policy = next(x for x in access_policies
                             if policy_name.lower() == x.key_name.lower())
    except StopIteration:
        raise CLIError('No policy found with name {}'.format(policy_name))

    connection_string = 'HostName={}.azure-devices.net;SharedAccessKeyName={};SharedAccessKey={}'.format(name,
                                                                                                         policy_name,
                                                                                                         access_policy.primary_key)
    return {'connectionString': connection_string}


def iot_device_create(client, resource_group_name, hub, device_id):
    device_client = get_iot_device_client(client, resource_group_name, hub, device_id)
    create_device_req = CreateDeviceRequest(device_id=device_id)
    result = device_client.create(device_id, create_device_req)
    return result


def iot_device_get_connection_string(client, resource_group_name, hub, device_id):
    device_client = get_iot_device_client(client, resource_group_name, hub, device_id)
    device_desc = device_client.get(device_id)
    if device_desc is None:
        raise CLIError('Nothing found for device {}'.format(device_id))

    connection_string = 'HostName={}.azure-devices.net;DeviceId={};SharedAccessKey={}'.format(hub, device_id,
                                                                                              device_desc.authentication.symmetric_key.primary_key)
    return {'connectionString': connection_string}


def get_iot_device_client(client, resource_group_name, hub, device_id):
    access_policies = client.list_keys(resource_group_name, hub).next()
    if access_policies is None:
        raise CLIError('No policy found from IoT Hub: {}.'.format(hub))
    logger.info('Shared Access Polices: %s', str(access_policies))
    try:
        access_policy = next(x for x in access_policies
                             if 'registrywrite' in x.rights.value.lower())
    except StopIteration:
        raise CLIError('No policy found with RegistryWrite permission.')

    base_url = '{0}.azure-devices.net'.format(hub)
    uri = '{0}/devices/{1}'.format(base_url, device_id)
    creds = SasTokenAuthentication(uri, access_policy.key_name, access_policy.primary_key)

    return IotHubDeviceClient(creds, client.config.subscription_id, base_url='https://' + base_url).iot_hub_devices
