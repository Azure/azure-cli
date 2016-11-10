#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
# pylint: disable=no-self-use,too-many-arguments,no-member,line-too-long

from __future__ import print_function
from os.path import exists
import azure.cli.core._logging as _logging
from azure.cli.core._util import CLIError
from azure.mgmt.iothub.models.iot_hub_client_enums import IotHubSku
from azure.mgmt.iothub.models.iot_hub_description import IotHubDescription
from azure.mgmt.iothub.models.iot_hub_sku_info import IotHubSkuInfo
from azure.cli.command_modules.iot.mgmt_iot_hub_device.lib.iot_hub_device_client import IotHubDeviceClient
from azure.cli.command_modules.iot.mgmt_iot_hub_device.lib.models.authentication import Authentication
from azure.cli.command_modules.iot.mgmt_iot_hub_device.lib.models.device_description import DeviceDescription
from azure.cli.command_modules.iot.mgmt_iot_hub_device.lib.models.x509_thumbprint import X509Thumbprint
from azure.cli.command_modules.iot.sas_token_auth import SasTokenAuthentication
from ._factory import resource_service_factory
from ._utils import create_self_signed_certificate

logger = _logging.get_az_logger(__name__)

# CUSTOM METHODS


def iot_hub_create(client, hub_name, resource_group_name,
                   location=None, sku=IotHubSku.f1.value, unit=1):
    name_availability = client.check_name_availability(hub_name)
    logger.info('name availability info: %s', name_availability)
    if name_availability is not None and not name_availability.name_available:
        raise CLIError(name_availability.message)
    location = _ensure_location(resource_group_name, location)
    iot_hub_description = IotHubDescription(location=location,
                                            sku=IotHubSkuInfo(name=sku, capacity=unit))
    result = client.create_or_update(resource_group_name=resource_group_name, resource_name=hub_name,
                                     iot_hub_description=iot_hub_description)
    return result


def iot_hub_get(client, hub_name, resource_group_name=None):
    if resource_group_name is None:
        return _get_iot_hub_by_name(client, hub_name)
    else:
        return client.get(resource_group_name, hub_name)


def iot_hub_list(client, resource_group_name=None):
    if resource_group_name is None:
        return client.list_by_subscription()
    else:
        return client.list_by_resource_group(resource_group_name)


def iot_hub_show_connection_string(client, hub_name=None, resource_group_name=None, policy_name='iothubowner'):
    if hub_name is None:
        hubs = iot_hub_list(client, resource_group_name)
        if hubs is None:
            raise CLIError('No IoT Hub found.')
        connection_strings = []
        for h in hubs:
            connection_string = _get_single_iot_hub_connection_string(client, h.name, h.resourcegroup, policy_name)
            connection_strings.append({"name": h.name,
                                       "connectionString": connection_string})
        return connection_strings
    else:
        resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
        connection_string = _get_single_iot_hub_connection_string(client, hub_name, resource_group_name, policy_name)
        return {"connectionString": connection_string}


def _get_single_iot_hub_connection_string(client, hub_name, resource_group_name, policy_name):
    access_policy = iot_hub_policy_get(client, hub_name, policy_name, resource_group_name)
    connection_string_template = 'HostName={}.azure-devices.net;SharedAccessKeyName={};SharedAccessKey={}'
    return connection_string_template.format(hub_name, policy_name, access_policy.primary_key)


def iot_hub_sku_list(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.get_valid_skus(resource_group_name, hub_name)


def iot_hub_consumer_group_create(client, hub_name, consumer_group_name, resource_group_name=None, event_hub_name='events'):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.create_event_hub_consumer_group(resource_group_name, hub_name, event_hub_name, consumer_group_name)


def iot_hub_consumer_group_list(client, hub_name, resource_group_name=None, event_hub_name='events'):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.list_event_hub_consumer_groups(resource_group_name, hub_name, event_hub_name)


def iot_hub_consumer_group_get(client, hub_name, consumer_group_name, resource_group_name=None, event_hub_name='events'):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.get_event_hub_consumer_group(resource_group_name, hub_name, event_hub_name, consumer_group_name)


def iot_hub_consumer_group_delete(client, hub_name, consumer_group_name, resource_group_name=None, event_hub_name='events'):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.delete_event_hub_consumer_group(resource_group_name, hub_name, event_hub_name, consumer_group_name)


def iot_hub_policy_list(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.list_keys(resource_group_name, hub_name)


def iot_hub_policy_get(client, hub_name, policy_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.get_keys_for_key_name(resource_group_name, hub_name, policy_name)


def iot_device_create(client, hub_name, device_id, resource_group_name=None, x509=False, primary_thumbprint=None,
                      secondary_thumbprint=None, valid_days=None, output_dir=None):
    if x509 is True:
        if (primary_thumbprint is not None or secondary_thumbprint is not None) and \
                (valid_days is not None or output_dir is not None):
            raise CLIError('Certificate thumbprint parameters are used for existing certificates.\n'
                           'Certificate valid days and output directory are used for creating self-signed certificate.\n'
                           'They must not be used together.')
        if output_dir is not None and not exists(output_dir):
            raise CLIError('Directory not exist: {0}'.format(output_dir))
    else:
        if primary_thumbprint is not None or secondary_thumbprint is not None or valid_days is not None or output_dir is not None:
            raise CLIError('X.509 certificate parameters must be used with --x509 flag.')

    device_client = _get_iot_device_client(client, resource_group_name, hub_name, device_id)
    device_description = DeviceDescription(device_id=device_id)

    if x509 is True:
        if primary_thumbprint is not None or secondary_thumbprint is not None:
            device_description.authentication = Authentication(x509_thumbprint=X509Thumbprint(primary_thumbprint,
                                                                                              secondary_thumbprint))
        else:
            valid_days = valid_days if valid_days is not None else 365
            output_dir = output_dir if output_dir is not None else '.'
            cert_info = create_self_signed_certificate(device_id, valid_days, output_dir)
            device_description.authentication = Authentication(x509_thumbprint=X509Thumbprint(cert_info['thumbprint']))

    results = device_client.create_or_update(device_id, device_description, if_match=None)

    # TODO: This is a work-around because thumbprint is not returned by IoT Device Registry REST API.
    #       Remove the following once this issue is fixed.
    if x509 is True:
        results.authentication.x509_thumbprint = device_description.authentication.x509_thumbprint
    return results


def iot_device_get(client, hub_name, device_id, resource_group_name=None):
    device_client = _get_iot_device_client(client, resource_group_name, hub_name, device_id)
    return device_client.get(device_id)


def iot_device_list(client, hub_name, resource_group_name=None, top=20):
    device_client = _get_iot_device_client(client, resource_group_name, hub_name, '')
    return device_client.list(top)


def iot_device_delete(client, hub_name, device_id, resource_group_name=None, etag='*'):
    device_client = _get_iot_device_client(client, resource_group_name, hub_name, device_id)
    return device_client.delete(device_id, etag)


def iot_device_show_connection_string(client, hub_name, device_id=None, resource_group_name=None, top=20):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    if device_id is None:
        devices = iot_device_list(client, hub_name, resource_group_name, top)
        if devices is None:
            raise CLIError('No devices found in IoT Hub {}.'.format(hub_name))
        connection_strings = []
        for d in devices:
            connection_string = _get_single_iot_device_connection_string(client, hub_name, d.device_id, resource_group_name)
            connection_strings.append({"deviceId": d.device_id,
                                       "connectionString": connection_string})
        return connection_strings
    else:
        connection_string = _get_single_iot_device_connection_string(client, hub_name, device_id, resource_group_name)
        return {"connectionString": connection_string}


def _get_single_iot_device_connection_string(client, hub_name, device_id, resource_group_name):
    device_client = _get_iot_device_client(client, resource_group_name, hub_name, device_id)
    device_desc = device_client.get(device_id)
    if device_desc is None:
        raise CLIError('Device {} not found.'.format(device_id))

    connection_string_template = 'HostName={0}.azure-devices.net;DeviceId={1};{2}'
    auth = device_desc.authentication
    if auth.symmetric_key.primary_key is not None:
        return connection_string_template.format(hub_name, device_id,
                                                 'SharedAccessKey=' + auth.symmetric_key.primary_key)
    elif auth.symmetric_key.secondary_key is not None:
        return connection_string_template.format(hub_name, device_id,
                                                 'SharedAccessKey=' + auth.symmetric_key.secondary_key)
    else:
        return connection_string_template.format(hub_name, device_id, 'x509=true')


def _get_iot_device_client(client, resource_group_name, hub_name, device_id):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    base_url = '{0}.azure-devices.net'.format(hub_name)
    uri = '{0}/devices/{1}'.format(base_url, device_id)
    access_policy = iot_hub_policy_get(client, hub_name, 'iothubowner', resource_group_name)
    creds = SasTokenAuthentication(uri, access_policy.key_name, access_policy.primary_key)
    return IotHubDeviceClient(creds, client.config.subscription_id, base_url='https://' + base_url).iot_hub_devices


def _get_iot_hub_by_name(client, hub_name):
    all_hubs = iot_hub_list(client)
    if all_hubs is None:
        raise CLIError('No IoT Hub found in current subscription.')
    try:
        target_hub = next(x for x in all_hubs if hub_name.lower() == x.name.lower())
    except StopIteration:
        raise CLIError('No IoT Hub found with name {} in current subscription.'.format(hub_name))
    return target_hub


def _ensure_location(resource_group_name, location):
    if location is None:
        logger.info('Location is none. Use location of resource group as default.')
        resource_group_client = resource_service_factory().resource_groups
        return resource_group_client.get(resource_group_name).location
    else:
        return location


def _ensure_resource_group_name(client, resource_group_name, hub_name):
    if resource_group_name is None:
        return _get_iot_hub_by_name(client, hub_name).resourcegroup
    else:
        return resource_group_name
