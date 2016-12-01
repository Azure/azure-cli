# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use,too-many-arguments,no-member,line-too-long

from __future__ import print_function
from os.path import exists
from enum import Enum
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


# CUSTOM TYPE
class KeyType(Enum):  # pylint: disable=too-few-public-methods
    primary = 'primary'
    secondary = 'secondary'


# CUSTOM METHODS
def iot_hub_create(client, hub_name, resource_group_name, location=None, sku=IotHubSku.f1.value, unit=1):
    _check_name_availability(client, hub_name)
    location = _ensure_location(resource_group_name, location)
    hub_description = IotHubDescription(location=location, sku=IotHubSkuInfo(name=sku, capacity=unit))
    return client.create_or_update(resource_group_name, hub_name, hub_description)


def _check_name_availability(client, hub_name):
    name_availability = client.check_name_availability(hub_name)
    if name_availability is not None and not name_availability.name_available:
        raise CLIError(name_availability.message)


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


def iot_hub_show_connection_string(client, hub_name=None, resource_group_name=None, policy_name='iothubowner',
                                   key_type=KeyType.primary.value):
    if hub_name is None:
        hubs = iot_hub_list(client, resource_group_name)
        if hubs is None:
            raise CLIError('No IoT Hub found.')

        def conn_str_getter(h):
            return _get_single_hub_connection_string(client, h.name, h.resourcegroup, policy_name, key_type)
        return [{'name': h.name, 'connectionString': conn_str_getter(h)} for h in hubs]
    else:
        resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
        conn_str = _get_single_hub_connection_string(client, hub_name, resource_group_name, policy_name, key_type)
        return {'connectionString': conn_str}


def _get_single_hub_connection_string(client, hub_name, resource_group_name, policy_name, key_type):
    access_policy = iot_hub_policy_get(client, hub_name, policy_name, resource_group_name)
    conn_str_template = 'HostName={}.azure-devices.net;SharedAccessKeyName={};SharedAccessKey={}'
    key = access_policy.secondary_key if key_type == KeyType.secondary else access_policy.primary_key
    return conn_str_template.format(hub_name, policy_name, key)


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


def iot_hub_job_list(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.list_jobs(resource_group_name, hub_name)


def iot_hub_job_get(client, hub_name, job_id, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.get_job(resource_group_name, hub_name, job_id)


def iot_hub_job_cancel(client, hub_name, job_id, resource_group_name=None):
    device_client = _get_device_client(client, resource_group_name, hub_name, '')
    return device_client.cancel_job(job_id)


def iot_hub_get_quota_metrics(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.get_quota_metrics(resource_group_name, hub_name)


def iot_hub_get_stats(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.get_stats(resource_group_name, hub_name)


def iot_device_create(client, hub_name, device_id, resource_group_name=None, x509=False, primary_thumbprint=None,
                      secondary_thumbprint=None, valid_days=None, output_dir=None):
    _validate_x509_parameters(x509, primary_thumbprint, secondary_thumbprint, valid_days, output_dir)
    device_client = _get_device_client(client, resource_group_name, hub_name, device_id)
    device = DeviceDescription(device_id=device_id)

    if x509 is True:
        device.authentication = _construct_x509_auth(device_id, primary_thumbprint, secondary_thumbprint, valid_days, output_dir)

    return device_client.create_or_update(device_id, device, if_match=None)


def _validate_x509_parameters(x509, primary_thumbprint, secondary_thumbprint, valid_days, output_dir):
    if x509 is True:
        if any([primary_thumbprint, secondary_thumbprint]) and any([valid_days, output_dir]):
            raise CLIError('Certificate thumbprint parameters are used for existing certificates.\n'
                           'Certificate valid days and output directory are used to generate self-signed certificate.\n'
                           'They must not be used together.')
        if output_dir is not None and not exists(output_dir):
            raise CLIError('Directory not exist: {0}'.format(output_dir))
    else:
        if any([primary_thumbprint, secondary_thumbprint, valid_days, output_dir]):
            raise CLIError('X.509 certificate parameters must be used with --x509 flag.')


def _construct_x509_auth(device_id, primary_thumbprint, secondary_thumbprint, valid_days, output_dir):
    if any([primary_thumbprint, secondary_thumbprint]):
        return Authentication(x509_thumbprint=X509Thumbprint(primary_thumbprint, secondary_thumbprint))
    else:
        valid_days = valid_days if valid_days is not None else 365
        output_dir = output_dir if output_dir is not None else '.'
        cert_info = create_self_signed_certificate(device_id, valid_days, output_dir)
        return Authentication(x509_thumbprint=X509Thumbprint(cert_info['thumbprint']))


def iot_device_get(client, hub_name, device_id, resource_group_name=None):
    device_client = _get_device_client(client, resource_group_name, hub_name, device_id)
    return device_client.get(device_id)


def iot_device_update(client, hub_name, device_id, parameters, resource_group_name=None):
    device_client = _get_device_client(client, resource_group_name, hub_name, device_id)
    return device_client.create_or_update(device_id, parameters)


def iot_device_list(client, hub_name, resource_group_name=None, top=20):
    device_client = _get_device_client(client, resource_group_name, hub_name, '')
    return device_client.list(top)


def iot_device_delete(client, hub_name, device_id, resource_group_name=None, etag='*'):
    device_client = _get_device_client(client, resource_group_name, hub_name, device_id)
    return device_client.delete(device_id, etag)


def iot_device_show_connection_string(client, hub_name, device_id=None, resource_group_name=None, top=20,
                                      key_type=KeyType.primary.value):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    if device_id is None:
        devices = iot_device_list(client, hub_name, resource_group_name, top)
        if devices is None:
            raise CLIError('No devices found in IoT Hub {}.'.format(hub_name))

        def conn_str_getter(d):
            return _get_single_device_connection_string(client, hub_name, d.device_id, resource_group_name, key_type)
        return [{'deviceId': d.device_id, 'connectionString': conn_str_getter(d)} for d in devices]
    else:
        conn_str = _get_single_device_connection_string(client, hub_name, device_id, resource_group_name, key_type)
        return {'connectionString': conn_str}


def iot_device_send_message(client, hub_name, device_id, resource_group_name=None, data='Ping from Azure CLI',
                            message_id=None, correlation_id=None, user_id=None):
    device_client = _get_device_client(client, resource_group_name, hub_name, device_id)
    return device_client.send_message(device_id, data, message_id, correlation_id, user_id)


def iot_device_receive_message(client, hub_name, device_id, resource_group_name=None, lock_timeout=60):
    device_client = _get_device_client(client, resource_group_name, hub_name, device_id)
    result = device_client.receive_message(device_id, lock_timeout, raw=True)
    if result is not None and result.response.status_code == 200:
        return {
            'ack': result.headers['iothub-ack'],
            'correlationId': result.headers['iothub-correlationid'],
            'data': result.response.content,
            'deliveryCount': result.headers['iothub-deliverycount'],
            'enqueuedTime': result.headers['iothub-enqueuedtime'],
            'expiry': result.headers['iothub-expiry'],
            'lockToken': result.headers['ETag'].strip('"'),
            'messageId': result.headers['iothub-messageid'],
            'sequenceNumber': result.headers['iothub-sequencenumber'],
            'to': result.headers['iothub-to'],
            'userId': result.headers['iothub-userid']
        }


def iot_device_complete_message(client, hub_name, device_id, lock_token, resource_group_name=None):
    device_client = _get_device_client(client, resource_group_name, hub_name, device_id)
    return device_client.complete_or_reject_message(device_id, lock_token)


def iot_device_reject_message(client, hub_name, device_id, lock_token, resource_group_name=None):
    device_client = _get_device_client(client, resource_group_name, hub_name, device_id)
    return device_client.complete_or_reject_message(device_id, lock_token, '')


def iot_device_abandon_message(client, hub_name, device_id, lock_token, resource_group_name=None):
    device_client = _get_device_client(client, resource_group_name, hub_name, device_id)
    return device_client.abandon_message(device_id, lock_token)


def _get_single_device_connection_string(client, hub_name, device_id, resource_group_name, key_type):
    device_client = _get_device_client(client, resource_group_name, hub_name, device_id)
    device = device_client.get(device_id)
    if device is None:
        raise CLIError('Device {} not found.'.format(device_id))

    conn_str_template = 'HostName={0}.azure-devices.net;DeviceId={1};{2}={3}'
    keys = device.authentication.symmetric_key
    if any([keys.primary_key, keys.secondary_key]):
        key = keys.secondary_key if key_type == KeyType.secondary else keys.primary_key
        if key is None:
            raise CLIError('{0} key not found.'.format(key_type))
        return conn_str_template.format(hub_name, device_id, 'SharedAccessKey', key)
    else:
        return conn_str_template.format(hub_name, device_id, 'x509', 'true')


def _get_device_client(client, resource_group_name, hub_name, device_id):
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
        resource_group_client = resource_service_factory().resource_groups
        return resource_group_client.get(resource_group_name).location
    else:
        return location


def _ensure_resource_group_name(client, resource_group_name, hub_name):
    if resource_group_name is None:
        return _get_iot_hub_by_name(client, hub_name).resourcegroup
    else:
        return resource_group_name
