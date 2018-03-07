# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use,no-member,line-too-long,too-few-public-methods

from __future__ import print_function
from os.path import exists
from enum import Enum
from knack.util import CLIError
from azure.cli.core.commands import LongRunningOperation

from azure.mgmt.iothub.models import (IotHubSku,
                                      AccessRights,
                                      IotHubDescription,
                                      IotHubSkuInfo,
                                      SharedAccessSignatureAuthorizationRule,
                                      IotHubProperties,
                                      EventHubProperties)

from azure.mgmt.iothubprovisioningservices.models import (ProvisioningServiceDescription,
                                                          IotDpsPropertiesDescription,
                                                          IotHubDefinitionDescription,
                                                          IotDpsSkuInfo,
                                                          IotDpsSku,
                                                          SharedAccessSignatureAuthorizationRuleAccessRightsDescription)

from azure.cli.command_modules.iot.mgmt_iot_hub_device.lib.iot_hub_device_client import IotHubDeviceClient
from azure.cli.command_modules.iot.mgmt_iot_hub_device.lib.models.authentication import Authentication
from azure.cli.command_modules.iot.mgmt_iot_hub_device.lib.models.device_description import DeviceDescription
from azure.cli.command_modules.iot.mgmt_iot_hub_device.lib.models.x509_thumbprint import X509Thumbprint
from azure.cli.command_modules.iot.sas_token_auth import SasTokenAuthentication
from azure.cli.core.util import sdk_no_wait

from ._client_factory import resource_service_factory
from ._utils import create_self_signed_certificate, open_certificate


# CUSTOM TYPE
class KeyType(Enum):
    primary = 'primary'
    secondary = 'secondary'


# This is a work around to simplify the permission parameter for access policy creation, and also align with the other
# command modules.
# The original AccessRights enum is a combination of below four basic access rights.
# In order to avoid asking for comma- & space-separated strings from the user, a space-separated list is supported for
# assigning multiple permissions.
# The underlying IoT SDK should handle this. However it isn't right now. Remove this after it is fixed in IoT SDK.
class SimpleAccessRights(Enum):
    registry_read = AccessRights.registry_read.value
    registry_write = AccessRights.registry_write.value
    service_connect = AccessRights.service_connect.value
    device_connect = AccessRights.device_connect.value


# CUSTOM METHODS FOR DPS
def iot_dps_list(client, resource_group_name=None):
    if resource_group_name is None:
        return client.iot_dps_resource.list_by_subscription()
    return client.iot_dps_resource.list_by_resource_group(resource_group_name)


def iot_dps_get(client, dps_name, resource_group_name=None):
    if resource_group_name is None:
        return _get_iot_dps_by_name(client, dps_name, resource_group_name)
    return client.iot_dps_resource.get(dps_name, resource_group_name)


def iot_dps_create(cmd, client, dps_name, resource_group_name, location=None, sku=IotDpsSku.s1.value, unit=1):
    cli_ctx = cmd.cli_ctx
    _check_dps_name_availability(client.iot_dps_resource, dps_name)
    location = _ensure_location(cli_ctx, resource_group_name, location)
    dps_property = IotDpsPropertiesDescription()
    dps_description = ProvisioningServiceDescription(location, dps_property, IotDpsSkuInfo(sku, unit))
    return client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description)


def iot_dps_update(client, dps_name, parameters, resource_group_name):
    return client.iot_dps_resource.create_or_update(resource_group_name, dps_name, parameters)


def iot_dps_delete(client, dps_name, resource_group_name):
    return client.iot_dps_resource.delete(dps_name, resource_group_name)


# DPS access policy methods
def iot_dps_access_policy_list(client, dps_name, resource_group_name):
    iot_dps_get(client, dps_name, resource_group_name)
    return client.iot_dps_resource.list_keys(dps_name, resource_group_name)


def iot_dps_access_policy_get(client, dps_name, resource_group_name, access_policy_name):
    iot_dps_get(client, dps_name, resource_group_name)
    return client.iot_dps_resource.list_keys_for_key_name(dps_name, access_policy_name, resource_group_name)


def iot_dps_access_policy_create(cmd, client, dps_name, resource_group_name, access_policy_name, rights, primary_key=None, secondary_key=None, no_wait=False):
    dps_access_policies = []
    dps_access_policies.extend(iot_dps_access_policy_list(client, dps_name, resource_group_name))
    if _is_policy_existed(dps_access_policies, access_policy_name):
        raise CLIError("Access policy {0} already existed.".format(access_policy_name))

    access_policy_rights = _convert_rights_to_access_rights(rights)
    dps_access_policies.append(SharedAccessSignatureAuthorizationRuleAccessRightsDescription(
        access_policy_name, access_policy_rights, primary_key, secondary_key))

    dps = iot_dps_get(client, dps_name, resource_group_name)
    dps_property = IotDpsPropertiesDescription(None, None, dps.properties.iot_hubs, dps.properties.allocation_policy, dps_access_policies)
    dps_description = ProvisioningServiceDescription(dps.location, dps_property, dps.sku)

    if no_wait:
        return client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description)
    LongRunningOperation(cmd.cli_ctx)(client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description))
    return iot_dps_access_policy_get(client, dps_name, resource_group_name, access_policy_name)


def iot_dps_access_policy_update(cmd, client, dps_name, resource_group_name, access_policy_name, primary_key=None, secondary_key=None, rights=None, no_wait=False):
    dps_access_policies = []
    dps_access_policies.extend(iot_dps_access_policy_list(client, dps_name, resource_group_name))

    if not _is_policy_existed(dps_access_policies, access_policy_name):
        raise CLIError("Access policy {0} doesn't exist.".format(access_policy_name))

    for policy in dps_access_policies:
        if policy.key_name == access_policy_name:
            if primary_key is not None:
                policy.primary_key = primary_key
            if secondary_key is not None:
                policy.secondary_key = secondary_key
            if rights is not None:
                policy.rights = _convert_rights_to_access_rights(rights)

    dps = iot_dps_get(client, dps_name, resource_group_name)
    dps_property = IotDpsPropertiesDescription(None, None, dps.properties.iot_hubs, dps.properties.allocation_policy, dps_access_policies)
    dps_description = ProvisioningServiceDescription(dps.location, dps_property, dps.sku)

    if no_wait:
        return client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description)
    LongRunningOperation(cmd.cli_ctx)(client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description))
    return iot_dps_access_policy_get(client, dps_name, resource_group_name, access_policy_name)


def iot_dps_access_policy_delete(cmd, client, dps_name, resource_group_name, access_policy_name, no_wait=False):
    dps_access_policies = []
    dps_access_policies.extend(iot_dps_access_policy_list(client, dps_name, resource_group_name))
    if not _is_policy_existed(dps_access_policies, access_policy_name):
        raise CLIError("Access policy {0} doesn't existed.".format(access_policy_name))
    updated_policies = [p for p in dps_access_policies if p.key_name.lower() != access_policy_name.lower()]

    dps = iot_dps_get(client, dps_name, resource_group_name)
    dps_property = IotDpsPropertiesDescription(None, None, dps.properties.iot_hubs, dps.properties.allocation_policy, updated_policies)
    dps_description = ProvisioningServiceDescription(dps.location, dps_property, dps.sku)

    if no_wait:
        return client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description)
    LongRunningOperation(cmd.cli_ctx)(client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description))
    return iot_dps_access_policy_list(client, dps_name, resource_group_name)


# DPS linked hub methods
def iot_dps_linked_hub_list(client, dps_name, resource_group_name):
    dps = iot_dps_get(client, dps_name, resource_group_name)
    return dps.properties.iot_hubs


def iot_dps_linked_hub_get(client, dps_name, resource_group_name, linked_hub):
    dps = iot_dps_get(client, dps_name, resource_group_name)
    for hub in dps.properties.iot_hubs:
        if hub.name == linked_hub:
            return hub
    raise CLIError("Linked hub '{0}' does not exist. Use 'iot dps linked-hub show to see all linked hubs.".format(linked_hub))


def iot_dps_linked_hub_create(cmd, client, dps_name, resource_group_name, connection_string, location, apply_allocation_policy=None, allocation_weight=None, no_wait=False):
    dps_linked_hubs = []
    dps_linked_hubs.extend(iot_dps_linked_hub_list(client, dps_name, resource_group_name))
    dps_linked_hubs.append(IotHubDefinitionDescription(connection_string, location, apply_allocation_policy, allocation_weight))

    dps = iot_dps_get(client, dps_name, resource_group_name)
    dps_property = IotDpsPropertiesDescription(None, None, dps_linked_hubs, dps.properties.allocation_policy, dps.properties.authorization_policies)
    dps_description = ProvisioningServiceDescription(dps.location, dps_property, dps.sku)

    if no_wait:
        return client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description)
    LongRunningOperation(cmd.cli_ctx)(client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description))
    return iot_dps_linked_hub_list(client, dps_name, resource_group_name)


def iot_dps_linked_hub_update(cmd, client, dps_name, resource_group_name, linked_hub, apply_allocation_policy=None, allocation_weight=None, no_wait=False):
    dps_linked_hubs = []
    dps_linked_hubs.extend(iot_dps_linked_hub_list(client, dps_name, resource_group_name))
    if not _is_linked_hub_existed(dps_linked_hubs, linked_hub):
        raise CLIError("Access policy {0} doesn't existed.".format(linked_hub))

    for hub in dps_linked_hubs:
        if hub.name == linked_hub:
            if apply_allocation_policy is not None:
                hub.apply_allocation_policy = apply_allocation_policy
            if allocation_weight is not None:
                hub.allocation_weight = allocation_weight

    dps = iot_dps_get(client, dps_name, resource_group_name)
    dps_property = IotDpsPropertiesDescription(None, None, dps_linked_hubs, dps.properties.allocation_policy, dps.properties.authorization_policies)
    dps_description = ProvisioningServiceDescription(dps.location, dps_property, dps.sku)

    if no_wait:
        return client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description)
    LongRunningOperation(cmd.cli_ctx)(client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description))
    return iot_dps_linked_hub_get(client, dps_name, resource_group_name, linked_hub)


def iot_dps_linked_hub_delete(cmd, client, dps_name, resource_group_name, linked_hub, no_wait=False):
    dps_linked_hubs = []
    dps_linked_hubs.extend(iot_dps_linked_hub_list(client, dps_name, resource_group_name))
    if not _is_linked_hub_existed(dps_linked_hubs, linked_hub):
        raise CLIError("Linked hub {0} doesn't existed.".format(linked_hub))
    updated_hub = [p for p in dps_linked_hubs if p.name.lower() != linked_hub.lower()]

    dps = iot_dps_get(client, dps_name, resource_group_name)
    dps_property = IotDpsPropertiesDescription(None, None, updated_hub, dps.properties.allocation_policy, dps.properties.authorization_policies)
    dps_description = ProvisioningServiceDescription(dps.location, dps_property, dps.sku)

    if no_wait:
        return client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description)
    LongRunningOperation(cmd.cli_ctx)(client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description))
    return iot_dps_linked_hub_list(client, dps_name, resource_group_name)


# DPS certificate methods
def iot_dps_certificate_list(client, dps_name, resource_group_name):
    return client.dps_certificates.list(resource_group_name, dps_name)


def iot_dps_certificate_get(client, dps_name, resource_group_name, certificate_name):
    return client.dps_certificate.get(certificate_name, resource_group_name, dps_name)


def iot_dps_certificate_create(client, dps_name, resource_group_name, certificate_name, certificate_path):
    cert_list = client.dps_certificates.list(resource_group_name, dps_name)
    for cert in cert_list.value:
        if cert.name == certificate_name:
            raise CLIError("Certificate '{0}' already exists. Use 'iot dps certificate update'"
                           " to update an existing certificate.".format(certificate_name))
    certificate = open_certificate(certificate_path)
    if not certificate:
        raise CLIError("Error uploading certificate '{0}'.".format(certificate_path))
    return client.dps_certificate.create_or_update(resource_group_name, dps_name, certificate_name, None, certificate)


def iot_dps_certificate_update(client, dps_name, resource_group_name, certificate_name, certificate_path, etag):
    cert_list = client.dps_certificates.list(resource_group_name, dps_name)
    for cert in cert_list.value:
        if cert.name == certificate_name:
            certificate = open_certificate(certificate_path)
            if not certificate:
                raise CLIError("Error uploading certificate '{0}'.".format(certificate_path))
            return client.dps_certificate.create_or_update(resource_group_name, dps_name, certificate_name, etag, certificate)
    raise CLIError("Certificate '{0}' does not exist. Use 'iot dps certificate create' to create a new certificate."
                   .format(certificate_name))


def iot_dps_certificate_delete(client, dps_name, resource_group_name, certificate_name, etag):
    return client.dps_certificate.delete(resource_group_name, etag, dps_name, certificate_name)


def iot_dps_certificate_gen_code(client, dps_name, resource_group_name, certificate_name, etag):
    return client.dps_certificate.generate_verification_code(certificate_name, etag, resource_group_name, dps_name)


def iot_dps_certificate_verify(client, dps_name, resource_group_name, certificate_name, certificate_path, etag):
    certificate = open_certificate(certificate_path)
    if not certificate:
        raise CLIError("Error uploading certificate '{0}'.".format(certificate_path))
    return client.dps_certificate.verify_certificate(certificate_name, etag, resource_group_name, dps_name,
                                                     None, None, None, None, None, None, None, None, certificate)


# CUSTOM METHODS
def iot_hub_certificate_list(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.certificates.list_by_iot_hub(resource_group_name, hub_name)


def iot_hub_certificate_get(client, hub_name, certificate_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.certificates.get(resource_group_name, hub_name, certificate_name)


def iot_hub_certificate_create(client, hub_name, certificate_name, certificate_path, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    # Get list of certs
    cert_list = client.certificates.list_by_iot_hub(resource_group_name, hub_name)
    for cert in cert_list.value:
        if cert.name == certificate_name:
            raise CLIError("Certificate '{0}' already exists. Use 'iot hub certificate update'"
                           " to update an existing certificate.".format(certificate_name))
    certificate = open_certificate(certificate_path)
    if not certificate:
        raise CLIError("Error uploading certificate '{0}'.".format(certificate_path))
    return client.certificates.create_or_update(resource_group_name, hub_name, certificate_name, None, certificate)


def iot_hub_certificate_update(client, hub_name, certificate_name, certificate_path, etag, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    cert_list = client.certificates.list_by_iot_hub(resource_group_name, hub_name)
    for cert in cert_list.value:
        if cert.name == certificate_name:
            certificate = open_certificate(certificate_path)
            if not certificate:
                raise CLIError("Error uploading certificate '{0}'.".format(certificate_path))
            return client.certificates.create_or_update(resource_group_name, hub_name, certificate_name, etag, certificate)
    raise CLIError("Certificate '{0}' does not exist. Use 'iot hub certificate create' to create a new certificate."
                   .format(certificate_name))


def iot_hub_certificate_delete(client, hub_name, certificate_name, etag, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.certificates.delete(resource_group_name, hub_name, certificate_name, etag)


def iot_hub_certificate_gen_code(client, hub_name, certificate_name, etag, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.certificates.generate_verification_code(resource_group_name, hub_name, certificate_name, etag)


def iot_hub_certificate_verify(client, hub_name, certificate_name, certificate_path, etag, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    certificate = open_certificate(certificate_path)
    if not certificate:
        raise CLIError("Error uploading certificate '{0}'.".format(certificate_path))
    return client.certificates.verify(resource_group_name, hub_name, certificate_name, etag, certificate)


def iot_hub_create(cmd, client, hub_name, resource_group_name, location=None, sku=IotHubSku.f1.value, unit=1, partition_count=2):
    cli_ctx = cmd.cli_ctx
    _check_name_availability(client.iot_hub_resource, hub_name)
    location = _ensure_location(cli_ctx, resource_group_name, location)
    sku = IotHubSkuInfo(name=sku, capacity=unit)

    event_hub_dic = {}
    event_hub_dic['events'] = EventHubProperties(1, partition_count)
    properties = IotHubProperties(None, None, event_hub_dic)
    hub_description = IotHubDescription(location, client.iot_hub_resource.config.subscription_id, resource_group_name,
                                        sku, None, None, properties)
    return client.iot_hub_resource.create_or_update(resource_group_name, hub_name, hub_description)


def _check_name_availability(iot_hub_resource, hub_name):
    name_availability = iot_hub_resource.check_name_availability(hub_name)
    if name_availability is not None and not name_availability.name_available:
        raise CLIError(name_availability.message)


def iot_hub_get(client, hub_name, resource_group_name=None):
    if resource_group_name is None:
        return _get_iot_hub_by_name(client, hub_name)
    return client.iot_hub_resource.get(resource_group_name, hub_name)


def iot_hub_list(client, resource_group_name=None):
    if resource_group_name is None:
        return client.iot_hub_resource.list_by_subscription()
    return client.iot_hub_resource.list_by_resource_group(resource_group_name)


def iot_hub_update(client, hub_name, parameters, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.create_or_update(resource_group_name, hub_name, parameters, {'IF-MATCH': parameters.etag})


def iot_hub_delete(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.delete(resource_group_name, hub_name)


# pylint: disable=inconsistent-return-statements
def iot_hub_show_connection_string(client, hub_name=None, resource_group_name=None, policy_name='iothubowner',
                                   key_type=KeyType.primary.value):
    if hub_name is None:
        hubs = iot_hub_list(client, resource_group_name)
        if hubs is None:
            raise CLIError("No IoT Hub found.")

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
    return client.iot_hub_resource.get_valid_skus(resource_group_name, hub_name)


def iot_hub_consumer_group_create(client, hub_name, consumer_group_name, resource_group_name=None, event_hub_name='events'):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.create_event_hub_consumer_group(resource_group_name, hub_name, event_hub_name, consumer_group_name)


def iot_hub_consumer_group_list(client, hub_name, resource_group_name=None, event_hub_name='events'):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.list_event_hub_consumer_groups(resource_group_name, hub_name, event_hub_name)


def iot_hub_consumer_group_get(client, hub_name, consumer_group_name, resource_group_name=None, event_hub_name='events'):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.get_event_hub_consumer_group(resource_group_name, hub_name, event_hub_name, consumer_group_name)


def iot_hub_consumer_group_delete(client, hub_name, consumer_group_name, resource_group_name=None, event_hub_name='events'):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.delete_event_hub_consumer_group(resource_group_name, hub_name, event_hub_name, consumer_group_name)


def iot_hub_policy_list(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.list_keys(resource_group_name, hub_name)


def iot_hub_policy_get(client, hub_name, policy_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.get_keys_for_key_name(resource_group_name, hub_name, policy_name)


def iot_hub_policy_create(client, hub_name, policy_name, permissions, resource_group_name=None):
    rights = _convert_perms_to_access_rights(permissions)
    hub = iot_hub_get(client, hub_name, resource_group_name)
    policies = []
    policies.extend(iot_hub_policy_list(client, hub_name, hub.resourcegroup))
    if _is_policy_existed(policies, policy_name):
        raise CLIError("Policy {0} already existed.".format(policy_name))
    policies.append(SharedAccessSignatureAuthorizationRule(policy_name, rights))
    hub.properties.authorization_policies = policies
    return client.iot_hub_resource.create_or_update(hub.resourcegroup, hub_name, hub, {'IF-MATCH': hub.etag})


def iot_hub_policy_delete(client, hub_name, policy_name, resource_group_name=None):
    import copy
    hub = iot_hub_get(client, hub_name, resource_group_name)
    policies = iot_hub_policy_list(client, hub_name, hub.resourcegroup)
    if not _is_policy_existed(copy.deepcopy(policies), policy_name):
        raise CLIError("Policy {0} not found.".format(policy_name))
    updated_policies = [p for p in policies if p.key_name.lower() != policy_name.lower()]
    hub.properties.authorization_policies = updated_policies
    return client.iot_hub_resource.create_or_update(hub.resourcegroup, hub_name, hub, {'IF-MATCH': hub.etag})


def _is_policy_existed(policies, policy_name):
    policy_set = set([p.key_name.lower() for p in policies])
    return policy_name.lower() in policy_set


def iot_hub_job_list(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.list_jobs(resource_group_name, hub_name)


def iot_hub_job_get(client, hub_name, job_id, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.get_job(resource_group_name, hub_name, job_id)


def iot_hub_job_cancel(client, hub_name, job_id, resource_group_name=None):
    device_client = _get_device_client(client, resource_group_name, hub_name, '')
    return device_client.cancel_job(job_id)


def iot_hub_get_quota_metrics(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.get_quota_metrics(resource_group_name, hub_name)


def iot_hub_get_stats(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.get_stats(resource_group_name, hub_name)


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
            raise CLIError("Certificate thumbprint parameters are used for existing certificates.\n"
                           "Certificate valid days and output directory are used to generate self-signed certificate.\n"
                           "They must not be used together.")
        if output_dir is not None and not exists(output_dir):
            raise CLIError("Directory not exist: {0}".format(output_dir))
    else:
        if any([primary_thumbprint, secondary_thumbprint, valid_days, output_dir]):
            raise CLIError("X.509 certificate parameters must be used with --x509 flag.")


def _construct_x509_auth(device_id, primary_thumbprint, secondary_thumbprint, valid_days, output_dir):
    if any([primary_thumbprint, secondary_thumbprint]):
        return Authentication(x509_thumbprint=X509Thumbprint(primary_thumbprint, secondary_thumbprint))
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


# pylint: disable=inconsistent-return-statements
def iot_device_show_connection_string(client, hub_name, device_id=None, resource_group_name=None, top=20,
                                      key_type=KeyType.primary.value):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    if device_id is None:
        devices = iot_device_list(client, hub_name, resource_group_name, top)
        if devices is None:
            raise CLIError("No devices found in IoT Hub {}.".format(hub_name))

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


# pylint: disable=inconsistent-return-statements
def iot_device_receive_message(client, hub_name, device_id, resource_group_name=None, lock_timeout=60):
    device_client = _get_device_client(client, resource_group_name, hub_name, device_id)
    result = sdk_no_wait(True, device_client.receive_message, device_id, lock_timeout)
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


def iot_device_export(client, hub_name, blob_container_uri, include_keys=False, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.export_devices(resource_group_name, hub_name, blob_container_uri, not include_keys)


def iot_device_import(client, hub_name, input_blob_container_uri, output_blob_container_uri, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.import_devices(resource_group_name, hub_name, input_blob_container_uri, output_blob_container_uri)


def _get_single_device_connection_string(client, hub_name, device_id, resource_group_name, key_type):
    device_client = _get_device_client(client, resource_group_name, hub_name, device_id)
    device = device_client.get(device_id)
    if device is None:
        raise CLIError("Device {} not found.".format(device_id))

    conn_str_template = "HostName={0}.azure-devices.net;DeviceId={1};{2}={3}"
    keys = device.authentication.symmetric_key
    if any([keys.primary_key, keys.secondary_key]):
        key = keys.secondary_key if key_type == KeyType.secondary else keys.primary_key
        if key is None:
            raise CLIError("{0} key not found.".format(key_type))
        return conn_str_template.format(hub_name, device_id, 'SharedAccessKey', key)
    else:
        return conn_str_template.format(hub_name, device_id, 'x509', 'true')


def _get_device_client(client, resource_group_name, hub_name, device_id):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    base_url = '{0}.azure-devices.net'.format(hub_name)
    uri = '{0}/devices/{1}'.format(base_url, device_id)
    access_policy = iot_hub_policy_get(client, hub_name, 'iothubowner', resource_group_name)
    creds = SasTokenAuthentication(uri, access_policy.key_name, access_policy.primary_key)
    return IotHubDeviceClient(creds, client.iot_hub_resource.config.subscription_id, base_url='https://' + base_url).iot_hub_devices


def _get_iot_hub_by_name(client, hub_name):
    all_hubs = iot_hub_list(client)
    if all_hubs is None:
        raise CLIError("No IoT Hub found in current subscription.")
    try:
        target_hub = next(x for x in all_hubs if hub_name.lower() == x.name.lower())
    except StopIteration:
        raise CLIError("No IoT Hub found with name {} in current subscription.".format(hub_name))
    return target_hub


def _ensure_location(cli_ctx, resource_group_name, location):
    if location is None:
        resource_group_client = resource_service_factory(cli_ctx).resource_groups
        return resource_group_client.get(resource_group_name).location
    return location


def _ensure_resource_group_name(client, resource_group_name, hub_name):
    if resource_group_name is None:
        return _get_iot_hub_by_name(client, hub_name).resourcegroup
    return resource_group_name


# Convert permission list to AccessRights from IoT SDK.
def _convert_perms_to_access_rights(perm_list):
    perm_set = set(perm_list)  # remove duplicate
    sorted_perm_list = sorted(perm_set)
    perm_key = '_'.join(sorted_perm_list)
    access_rights_mapping = {
        'registryread': AccessRights.registry_read,
        'registrywrite': AccessRights.registry_write,
        'serviceconnect': AccessRights.service_connect,
        'deviceconnect': AccessRights.device_connect,
        'registryread_registrywrite': AccessRights.registry_read_registry_write,
        'registryread_serviceconnect': AccessRights.registry_read_service_connect,
        'deviceconnect_registryread': AccessRights.registry_read_device_connect,
        'registrywrite_serviceconnect': AccessRights.registry_write_service_connect,
        'deviceconnect_registrywrite': AccessRights.registry_write_device_connect,
        'deviceconnect_serviceconnect': AccessRights.service_connect_device_connect,
        'registryread_registrywrite_serviceconnect': AccessRights.registry_read_registry_write_service_connect,
        'deviceconnect_registryread_registrywrite': AccessRights.registry_read_registry_write_device_connect,
        'deviceconnect_registryread_serviceconnect': AccessRights.registry_read_service_connect_device_connect,
        'deviceconnect_registrywrite_serviceconnect': AccessRights.registry_write_service_connect_device_connect,
        'deviceconnect_registryread_registrywrite_serviceconnect': AccessRights.registry_read_registry_write_service_connect_device_connect
    }
    return access_rights_mapping[perm_key]


def _is_linked_hub_existed(hubs, hub_name):
    hub_set = set([h.name.lower() for h in hubs])
    return hub_name.lower() in hub_set


def _get_iot_dps_by_name(client, dps_name, resource_group=None):
    all_dps = iot_dps_list(client, resource_group)
    if all_dps is None:
        raise CLIError("No DPS found in current subscription.")
    try:
        target_dps = next(x for x in all_dps if dps_name.lower() == x.name.lower())
    except StopIteration:
        raise CLIError("No DPS found with name {} in current subscription.".format(dps_name))
    return target_dps


def _check_dps_name_availability(iot_dps_resource, dps_name):
    name_availability = iot_dps_resource.check_provisioning_service_name_availability(dps_name)
    if name_availability is not None and not name_availability.name_available:
        raise CLIError(name_availability.message)


def _convert_rights_to_access_rights(right_list):
    right_set = set(right_list)  # remove duplicate
    return ",".join(list(right_set))
