# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use,no-member,line-too-long,too-few-public-methods,too-many-lines,too-many-arguments,too-many-locals

from enum import Enum
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.util import sdk_no_wait

from azure.mgmt.iothub.models import (IotHubSku,
                                      AccessRights,
                                      CloudToDeviceProperties,
                                      IotHubDescription,
                                      IotHubSkuInfo,
                                      SharedAccessSignatureAuthorizationRule,
                                      IotHubProperties,
                                      EventHubProperties,
                                      FeedbackProperties,
                                      MessagingEndpointProperties,
                                      EnrichmentProperties,
                                      RoutingEventHubProperties,
                                      RoutingServiceBusQueueEndpointProperties,
                                      RoutingServiceBusTopicEndpointProperties,
                                      RoutingStorageContainerProperties,
                                      RouteProperties,
                                      RoutingMessage,
                                      StorageEndpointProperties,
                                      TestRouteInput,
                                      TestAllRoutesInput)


from azure.mgmt.iothubprovisioningservices.models import (ProvisioningServiceDescription,
                                                          IotDpsPropertiesDescription,
                                                          IotHubDefinitionDescription,
                                                          IotDpsSkuInfo,
                                                          IotDpsSku,
                                                          SharedAccessSignatureAuthorizationRuleAccessRightsDescription)


from azure.mgmt.iotcentral.models import (AppSkuInfo,
                                          App)

from azure.cli.command_modules.iot.shared import EndpointType, EncodingFormat, RenewKeyType, AuthenticationType
from ._client_factory import resource_service_factory
from ._utils import open_certificate, generate_key


logger = get_logger(__name__)


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


def iot_dps_create(cmd, client, dps_name, resource_group_name, location=None, sku=IotDpsSku.s1.value, unit=1, tags=None):
    cli_ctx = cmd.cli_ctx
    _check_dps_name_availability(client.iot_dps_resource, dps_name)
    location = _ensure_location(cli_ctx, resource_group_name, location)
    dps_property = IotDpsPropertiesDescription()
    dps_description = ProvisioningServiceDescription(location=location,
                                                     properties=dps_property,
                                                     sku=IotDpsSkuInfo(name=sku, capacity=unit),
                                                     tags=tags)
    return client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description)


def iot_dps_update(client, dps_name, parameters, resource_group_name, tags=None):
    if tags is not None:
        parameters.tags = tags
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
        key_name=access_policy_name, rights=access_policy_rights, primary_key=primary_key, secondary_key=secondary_key))

    dps = iot_dps_get(client, dps_name, resource_group_name)
    dps_property = IotDpsPropertiesDescription(iot_hubs=dps.properties.iot_hubs,
                                               allocation_policy=dps.properties.allocation_policy,
                                               authorization_policies=dps_access_policies)
    dps_description = ProvisioningServiceDescription(location=dps.location, properties=dps_property, sku=dps.sku)

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
    dps_property = IotDpsPropertiesDescription(iot_hubs=dps.properties.iot_hubs,
                                               allocation_policy=dps.properties.allocation_policy,
                                               authorization_policies=dps_access_policies)
    dps_description = ProvisioningServiceDescription(location=dps.location, properties=dps_property, sku=dps.sku)

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
    dps_property = IotDpsPropertiesDescription(iot_hubs=dps.properties.iot_hubs,
                                               allocation_policy=dps.properties.allocation_policy,
                                               authorization_policies=updated_policies)
    dps_description = ProvisioningServiceDescription(location=dps.location, properties=dps_property, sku=dps.sku)

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

    # Hack due to DPS Swagger/SDK issue
    # In the newer API version the name parameter is required
    # however in the SDK name is read-only/assigned to None
    client.api_version = '2017-11-15'
    dps_linked_hubs.append(IotHubDefinitionDescription(connection_string=connection_string,
                                                       location=location,
                                                       apply_allocation_policy=apply_allocation_policy,
                                                       allocation_weight=allocation_weight))

    dps = iot_dps_get(client, dps_name, resource_group_name)
    dps_property = IotDpsPropertiesDescription(iot_hubs=dps_linked_hubs,
                                               allocation_policy=dps.properties.allocation_policy,
                                               authorization_policies=dps.properties.authorization_policies)
    dps_description = ProvisioningServiceDescription(location=dps.location, properties=dps_property, sku=dps.sku)

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
    dps_property = IotDpsPropertiesDescription(iot_hubs=dps_linked_hubs,
                                               allocation_policy=dps.properties.allocation_policy,
                                               authorization_policies=dps.properties.authorization_policies)
    dps_description = ProvisioningServiceDescription(location=dps.location, properties=dps_property, sku=dps.sku)

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
    dps_property = IotDpsPropertiesDescription(iot_hubs=updated_hub,
                                               allocation_policy=dps.properties.allocation_policy,
                                               authorization_policies=dps.properties.authorization_policies)
    dps_description = ProvisioningServiceDescription(location=dps.location, properties=dps_property, sku=dps.sku)

    if no_wait:
        return client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description)
    LongRunningOperation(cmd.cli_ctx)(client.iot_dps_resource.create_or_update(resource_group_name, dps_name, dps_description))
    return iot_dps_linked_hub_list(client, dps_name, resource_group_name)


# DPS certificate methods
def iot_dps_certificate_list(client, dps_name, resource_group_name):
    return client.dps_certificate.list(resource_group_name, dps_name)


def iot_dps_certificate_get(client, dps_name, resource_group_name, certificate_name):
    return client.dps_certificate.get(certificate_name, resource_group_name, dps_name)


def iot_dps_certificate_create(client, dps_name, resource_group_name, certificate_name, certificate_path):
    cert_list = client.dps_certificate.list(resource_group_name, dps_name)
    for cert in cert_list.value:
        if cert.name == certificate_name:
            raise CLIError("Certificate '{0}' already exists. Use 'iot dps certificate update'"
                           " to update an existing certificate.".format(certificate_name))
    certificate = open_certificate(certificate_path)
    if not certificate:
        raise CLIError("Error uploading certificate '{0}'.".format(certificate_path))
    return client.dps_certificate.create_or_update(resource_group_name, dps_name, certificate_name, None, certificate)


def iot_dps_certificate_update(client, dps_name, resource_group_name, certificate_name, certificate_path, etag):
    cert_list = client.dps_certificate.list(resource_group_name, dps_name)
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


def iot_hub_create(cmd, client, hub_name, resource_group_name, location=None,
                   sku=IotHubSku.s1.value,
                   unit=1,
                   partition_count=4,
                   retention_day=1,
                   c2d_ttl=1,
                   c2d_max_delivery_count=10,
                   feedback_lock_duration=5,
                   feedback_ttl=1,
                   feedback_max_delivery_count=10,
                   enable_fileupload_notifications=False,
                   fileupload_notification_max_delivery_count=10,
                   fileupload_notification_ttl=1,
                   fileupload_storage_connectionstring=None,
                   fileupload_storage_container_name=None,
                   fileupload_sas_ttl=1,
                   fileupload_storage_authentication_type=None,
                   fileupload_storage_container_uri=None,
                   min_tls_version=None,
                   tags=None):
    from datetime import timedelta
    cli_ctx = cmd.cli_ctx
    if enable_fileupload_notifications:
        if not fileupload_storage_connectionstring or not fileupload_storage_container_name:
            raise CLIError('Please specify storage endpoint(storage connection string and storage container name).')
    if fileupload_storage_connectionstring and not fileupload_storage_container_name:
        raise CLIError('Please mention storage container name.')
    if fileupload_storage_container_name and not fileupload_storage_connectionstring:
        raise CLIError('Please mention storage connection string.')
    identity_based_file_upload = fileupload_storage_authentication_type and fileupload_storage_authentication_type.lower() == AuthenticationType.IdentityBased.value
    if not identity_based_file_upload and not fileupload_storage_connectionstring and fileupload_storage_container_name:
        raise CLIError('Key-based authentication requires a connection string.')
    if identity_based_file_upload and not fileupload_storage_container_uri:
        raise CLIError('Identity-based authentication requires a storage container uri (--fileupload-storage-container-uri, --fcu).')
    location = _ensure_location(cli_ctx, resource_group_name, location)
    sku = IotHubSkuInfo(name=sku, capacity=unit)

    event_hub_dic = {}
    event_hub_dic['events'] = EventHubProperties(retention_time_in_days=retention_day,
                                                 partition_count=partition_count)
    feedback_Properties = FeedbackProperties(lock_duration_as_iso8601=timedelta(seconds=feedback_lock_duration),
                                             ttl_as_iso8601=timedelta(hours=feedback_ttl),
                                             max_delivery_count=feedback_max_delivery_count)
    cloud_to_device_properties = CloudToDeviceProperties(max_delivery_count=c2d_max_delivery_count,
                                                         default_ttl_as_iso8601=timedelta(hours=c2d_ttl),
                                                         feedback=feedback_Properties)
    msg_endpoint_dic = {}
    msg_endpoint_dic['fileNotifications'] = MessagingEndpointProperties(max_delivery_count=fileupload_notification_max_delivery_count,
                                                                        ttl_as_iso8601=timedelta(hours=fileupload_notification_ttl))
    storage_endpoint_dic = {}
    storage_endpoint_dic['$default'] = StorageEndpointProperties(
        sas_ttl_as_iso8601=timedelta(hours=fileupload_sas_ttl),
        connection_string=fileupload_storage_connectionstring if fileupload_storage_connectionstring else '',
        container_name=fileupload_storage_container_name if fileupload_storage_container_name else '',
        authentication_type=fileupload_storage_authentication_type if fileupload_storage_authentication_type else None,
        container_uri=fileupload_storage_container_uri if fileupload_storage_container_uri else '')

    properties = IotHubProperties(event_hub_endpoints=event_hub_dic,
                                  messaging_endpoints=msg_endpoint_dic,
                                  storage_endpoints=storage_endpoint_dic,
                                  cloud_to_device=cloud_to_device_properties,
                                  min_tls_version=min_tls_version)
    properties.enable_file_upload_notifications = enable_fileupload_notifications

    hub_description = IotHubDescription(location=location,
                                        sku=sku,
                                        properties=properties,
                                        tags=tags)

    return client.iot_hub_resource.create_or_update(resource_group_name, hub_name, hub_description)


def iot_hub_get(cmd, client, hub_name, resource_group_name=None):
    cli_ctx = cmd.cli_ctx
    if resource_group_name is None:
        return _get_iot_hub_by_name(client, hub_name)
    if not _ensure_resource_group_existence(cli_ctx, resource_group_name):
        raise CLIError("Resource group '{0}' could not be found.".format(resource_group_name))
    name_availability = client.iot_hub_resource.check_name_availability(hub_name)
    if name_availability is not None and name_availability.name_available:
        raise CLIError("An IotHub '{0}' under resource group '{1}' was not found."
                       .format(hub_name, resource_group_name))
    return client.iot_hub_resource.get(resource_group_name, hub_name)


def iot_hub_list(client, resource_group_name=None):
    if resource_group_name is None:
        return client.iot_hub_resource.list_by_subscription()
    return client.iot_hub_resource.list_by_resource_group(resource_group_name)


def update_iot_hub_custom(instance,
                          sku=None,
                          unit=None,
                          retention_day=None,
                          c2d_ttl=None,
                          c2d_max_delivery_count=None,
                          feedback_lock_duration=None,
                          feedback_ttl=None,
                          feedback_max_delivery_count=None,
                          enable_fileupload_notifications=None,
                          fileupload_notification_max_delivery_count=None,
                          fileupload_notification_ttl=None,
                          fileupload_storage_connectionstring=None,
                          fileupload_storage_container_name=None,
                          fileupload_sas_ttl=None,
                          fileupload_storage_authentication_type=None,
                          fileupload_storage_container_uri=None,
                          tags=None):
    from datetime import timedelta
    if tags is not None:
        instance.tags = tags
    if sku is not None:
        instance.sku.name = sku
    if unit is not None:
        instance.sku.capacity = unit
    if retention_day is not None:
        instance.properties.event_hub_endpoints['events'].retention_time_in_days = retention_day
    if c2d_ttl is not None:
        instance.properties.cloud_to_device.default_ttl_as_iso8601 = timedelta(hours=c2d_ttl)
    if c2d_max_delivery_count is not None:
        instance.properties.cloud_to_device.max_delivery_count = c2d_max_delivery_count
    if feedback_lock_duration is not None:
        duration = timedelta(seconds=feedback_lock_duration)
        instance.properties.cloud_to_device.feedback.lock_duration_as_iso8601 = duration
    if feedback_ttl is not None:
        instance.properties.cloud_to_device.feedback.ttl_as_iso8601 = timedelta(hours=feedback_ttl)
    if feedback_max_delivery_count is not None:
        instance.properties.cloud_to_device.feedback.max_delivery_count = feedback_max_delivery_count
    if enable_fileupload_notifications is not None:
        instance.properties.enable_file_upload_notifications = enable_fileupload_notifications
    if fileupload_notification_max_delivery_count is not None:
        count = fileupload_notification_max_delivery_count
        instance.properties.messaging_endpoints['fileNotifications'].max_delivery_count = count
    if fileupload_notification_ttl is not None:
        ttl = timedelta(hours=fileupload_notification_ttl)
        instance.properties.messaging_endpoints['fileNotifications'].ttl_as_iso8601 = ttl

    identity_based_file_upload = fileupload_storage_authentication_type and fileupload_storage_authentication_type.lower() == AuthenticationType.IdentityBased.value
    if identity_based_file_upload:
        instance.properties.storage_endpoints['$default'].authentication_type = AuthenticationType.IdentityBased
        instance.properties.storage_endpoints['$default'].container_uri = fileupload_storage_container_uri
    elif fileupload_storage_authentication_type is not None:
        instance.properties.storage_endpoints['$default'].authentication_type = None
        instance.properties.storage_endpoints['$default'].container_uri = None
    # TODO - remove connection string and set containerURI once fileUpload SAS URL is enabled
    if fileupload_storage_connectionstring is not None and fileupload_storage_container_name is not None:
        instance.properties.storage_endpoints['$default'].connection_string = fileupload_storage_connectionstring
        instance.properties.storage_endpoints['$default'].container_name = fileupload_storage_container_name
    elif fileupload_storage_connectionstring is not None:
        raise CLIError('Please mention storage container name.')
    elif fileupload_storage_container_name is not None:
        raise CLIError('Please mention storage connection string.')
    if fileupload_sas_ttl is not None:
        instance.properties.storage_endpoints['$default'].sas_ttl_as_iso8601 = timedelta(hours=fileupload_sas_ttl)
    return instance


def iot_hub_update(client, hub_name, parameters, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.create_or_update(resource_group_name, hub_name, parameters, {'IF-MATCH': parameters.etag})


def iot_hub_delete(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.delete(resource_group_name, hub_name)


# pylint: disable=inconsistent-return-statements
def iot_hub_show_connection_string(client, hub_name=None, resource_group_name=None, policy_name='iothubowner',
                                   key_type=KeyType.primary.value, show_all=False):
    if hub_name is None:
        hubs = iot_hub_list(client, resource_group_name)
        if hubs is None:
            raise CLIError("No IoT Hub found.")

        def conn_str_getter(h):
            return _get_hub_connection_string(client, h.name, h.additional_properties['resourcegroup'], policy_name, key_type, show_all)
        return [{'name': h.name, 'connectionString': conn_str_getter(h)} for h in hubs]
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    conn_str = _get_hub_connection_string(client, hub_name, resource_group_name, policy_name, key_type, show_all)
    return {'connectionString': conn_str if show_all else conn_str[0]}


def _get_hub_connection_string(client, hub_name, resource_group_name, policy_name, key_type, show_all):
    policies = []
    if show_all:
        policies.extend(iot_hub_policy_list(client, hub_name, resource_group_name))
    else:
        policies.append(iot_hub_policy_get(client, hub_name, policy_name, resource_group_name))
    # Intermediate fix to support domains beyond azure-devices.netproperty
    hub = _get_iot_hub_by_name(client, hub_name)
    hostname = hub.properties.host_name
    conn_str_template = 'HostName={};SharedAccessKeyName={};SharedAccessKey={}'
    return [conn_str_template.format(hostname,
                                     p.key_name,
                                     p.secondary_key if key_type == KeyType.secondary else p.primary_key) for p in policies]


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


def iot_hub_policy_create(cmd, client, hub_name, policy_name, permissions, resource_group_name=None):
    rights = _convert_perms_to_access_rights(permissions)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    policies = []
    policies.extend(iot_hub_policy_list(client, hub_name, hub.additional_properties['resourcegroup']))
    if _is_policy_existed(policies, policy_name):
        raise CLIError("Policy {0} already existed.".format(policy_name))
    policies.append(SharedAccessSignatureAuthorizationRule(key_name=policy_name, rights=rights))
    hub.properties.authorization_policies = policies
    return client.iot_hub_resource.create_or_update(hub.additional_properties['resourcegroup'], hub_name, hub, {'IF-MATCH': hub.etag})


def iot_hub_policy_delete(cmd, client, hub_name, policy_name, resource_group_name=None):
    import copy
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    policies = iot_hub_policy_list(client, hub_name, hub.additional_properties['resourcegroup'])
    if not _is_policy_existed(copy.deepcopy(policies), policy_name):
        raise CLIError("Policy {0} not found.".format(policy_name))
    updated_policies = [p for p in policies if p.key_name.lower() != policy_name.lower()]
    hub.properties.authorization_policies = updated_policies
    return client.iot_hub_resource.create_or_update(hub.additional_properties['resourcegroup'], hub_name, hub, {'IF-MATCH': hub.etag})


def iot_hub_policy_key_renew(cmd, client, hub_name, policy_name, regenerate_key, resource_group_name=None, no_wait=False):
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    policies = []
    policies.extend(iot_hub_policy_list(client, hub_name, hub.additional_properties['resourcegroup']))
    if not _is_policy_existed(policies, policy_name):
        raise CLIError("Policy {0} not found.".format(policy_name))
    updated_policies = [p for p in policies if p.key_name.lower() != policy_name.lower()]
    requested_policy = [p for p in policies if p.key_name.lower() == policy_name.lower()]
    if regenerate_key == RenewKeyType.Primary.value:
        requested_policy[0].primary_key = generate_key()
    if regenerate_key == RenewKeyType.Secondary.value:
        requested_policy[0].secondary_key = generate_key()
    if regenerate_key == RenewKeyType.Swap.value:
        temp = requested_policy[0].primary_key
        requested_policy[0].primary_key = requested_policy[0].secondary_key
        requested_policy[0].secondary_key = temp
    updated_policies.append(SharedAccessSignatureAuthorizationRule(key_name=requested_policy[0].key_name,
                                                                   rights=requested_policy[0].rights,
                                                                   primary_key=requested_policy[0].primary_key,
                                                                   secondary_key=requested_policy[0].secondary_key))
    hub.properties.authorization_policies = updated_policies
    if no_wait:
        return client.iot_hub_resource.create_or_update(hub.additional_properties['resourcegroup'], hub_name, hub, {'IF-MATCH': hub.etag})
    LongRunningOperation(cmd.cli_ctx)(client.iot_hub_resource.create_or_update(hub.additional_properties['resourcegroup'], hub_name, hub, {'IF-MATCH': hub.etag}))
    return iot_hub_policy_get(client, hub_name, policy_name, resource_group_name)


def _is_policy_existed(policies, policy_name):
    policy_set = {p.key_name.lower() for p in policies}
    return policy_name.lower() in policy_set


def iot_hub_get_quota_metrics(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    iotHubQuotaMetricCollection = []
    iotHubQuotaMetricCollection.extend(client.iot_hub_resource.get_quota_metrics(resource_group_name, hub_name))
    for quotaMetric in iotHubQuotaMetricCollection:
        if quotaMetric.name == 'TotalDeviceCount':
            quotaMetric.max_value = 'Unlimited'
    return iotHubQuotaMetricCollection


def iot_hub_get_stats(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.get_stats(resource_group_name, hub_name)


def validate_authentication_type_input(endpoint_type, connection_string=None, authentication_type=None, endpoint_uri=None, entity_path=None):
    is_keyBased = (AuthenticationType.KeyBased.value == authentication_type.lower()) or (authentication_type is None)
    has_connection_string = (connection_string is not None)
    if is_keyBased and not has_connection_string:
        raise CLIError("Please provide a connection string '--connection-string/-c'")

    has_endpoint_uri = (endpoint_uri is not None)
    has_endpoint_uri_and_path = (has_endpoint_uri) and (entity_path is not None)
    if EndpointType.AzureStorageContainer.value == endpoint_type.lower() and not has_endpoint_uri:
        raise CLIError("Please provide an endpoint uri '--endpoint-uri'")
    if not has_endpoint_uri_and_path:
        raise CLIError("Please provide an endpoint uri '--endpoint-uri' and entity path '--entity-path'")


def iot_hub_routing_endpoint_create(cmd, client, hub_name, endpoint_name, endpoint_type,
                                    endpoint_resource_group, endpoint_subscription_id,
                                    connection_string=None, container_name=None, encoding=None,
                                    resource_group_name=None, batch_frequency=300, chunk_size_window=300,
                                    file_name_format='{iothub}/{partition}/{YYYY}/{MM}/{DD}/{HH}/{mm}',
                                    authentication_type=None, endpoint_uri=None, entity_path=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    if EndpointType.EventHub.value == endpoint_type.lower():
        hub.properties.routing.endpoints.event_hubs.append(
            RoutingEventHubProperties(
                connection_string=connection_string,
                name=endpoint_name,
                subscription_id=endpoint_subscription_id,
                resource_group=endpoint_resource_group,
                authentication_type=authentication_type,
                endpoint_uri=endpoint_uri,
                entity_path=entity_path
            )
        )
    elif EndpointType.ServiceBusQueue.value == endpoint_type.lower():
        hub.properties.routing.endpoints.service_bus_queues.append(
            RoutingServiceBusQueueEndpointProperties(
                connection_string=connection_string,
                name=endpoint_name,
                subscription_id=endpoint_subscription_id,
                resource_group=endpoint_resource_group,
                authentication_type=authentication_type,
                endpoint_uri=endpoint_uri,
                entity_path=entity_path
            )
        )
    elif EndpointType.ServiceBusTopic.value == endpoint_type.lower():
        hub.properties.routing.endpoints.service_bus_topics.append(
            RoutingServiceBusTopicEndpointProperties(
                connection_string=connection_string,
                name=endpoint_name,
                subscription_id=endpoint_subscription_id,
                resource_group=endpoint_resource_group,
                authentication_type=authentication_type,
                endpoint_uri=endpoint_uri,
                entity_path=entity_path
            )
        )
    elif EndpointType.AzureStorageContainer.value == endpoint_type.lower():
        if not container_name:
            raise CLIError("Container name is required.")
        hub.properties.routing.endpoints.storage_containers.append(
            RoutingStorageContainerProperties(
                connection_string=connection_string,
                name=endpoint_name,
                subscription_id=endpoint_subscription_id,
                resource_group=endpoint_resource_group,
                container_name=container_name,
                encoding=encoding.lower() if encoding else EncodingFormat.AVRO.value,
                file_name_format=file_name_format,
                batch_frequency_in_seconds=batch_frequency,
                max_chunk_size_in_bytes=(chunk_size_window * 1048576),
                authentication_type=authentication_type,
                endpoint_uri=endpoint_uri
            )
        )
    return client.iot_hub_resource.create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})


def iot_hub_routing_endpoint_list(cmd, client, hub_name, endpoint_type=None, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    if not endpoint_type:
        return hub.properties.routing.endpoints
    if EndpointType.EventHub.value == endpoint_type.lower():
        return hub.properties.routing.endpoints.event_hubs
    if EndpointType.ServiceBusQueue.value == endpoint_type.lower():
        return hub.properties.routing.endpoints.service_bus_queues
    if EndpointType.ServiceBusTopic.value == endpoint_type.lower():
        return hub.properties.routing.endpoints.service_bus_topics
    if EndpointType.AzureStorageContainer.value == endpoint_type.lower():
        return hub.properties.routing.endpoints.storage_containers


def iot_hub_routing_endpoint_show(cmd, client, hub_name, endpoint_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    for event_hub in hub.properties.routing.endpoints.event_hubs:
        if event_hub.name.lower() == endpoint_name.lower():
            return event_hub
    for service_bus_queue in hub.properties.routing.endpoints.service_bus_queues:
        if service_bus_queue.name.lower() == endpoint_name.lower():
            return service_bus_queue
    for service_bus_topic in hub.properties.routing.endpoints.service_bus_topics:
        if service_bus_topic.name.lower() == endpoint_name.lower():
            return service_bus_topic
    for storage_container in hub.properties.routing.endpoints.storage_containers:
        if storage_container.name.lower() == endpoint_name.lower():
            return storage_container
    raise CLIError("No endpoint found.")


def iot_hub_routing_endpoint_delete(cmd, client, hub_name, endpoint_name=None, endpoint_type=None, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    hub.properties.routing.endpoints = _delete_routing_endpoints(endpoint_name, endpoint_type, hub.properties.routing.endpoints)
    return client.iot_hub_resource.create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})


def iot_hub_route_create(cmd, client, hub_name, route_name, source_type, endpoint_name, enabled=None, condition=None,
                         resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    hub.properties.routing.routes.append(
        RouteProperties(
            source=source_type,
            name=route_name,
            endpoint_names=endpoint_name.split(),
            condition=('true' if condition is None else condition),
            is_enabled=(True if enabled is None else enabled)
        )
    )
    return client.iot_hub_resource.create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})


def iot_hub_route_list(cmd, client, hub_name, source_type=None, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    if source_type:
        return [route for route in hub.properties.routing.routes if route.source.lower() == source_type.lower()]
    return hub.properties.routing.routes


def iot_hub_route_show(cmd, client, hub_name, route_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    for route in hub.properties.routing.routes:
        if route.name.lower() == route_name.lower():
            return route
    raise CLIError("No route found.")


def iot_hub_route_delete(cmd, client, hub_name, route_name=None, source_type=None, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    if not route_name and not source_type:
        hub.properties.routing.routes = []
    if route_name:
        hub.properties.routing.routes = [route for route in hub.properties.routing.routes
                                         if route.name.lower() != route_name.lower()]
    if source_type:
        hub.properties.routing.routes = [route for route in hub.properties.routing.routes
                                         if route.source.lower() != source_type.lower()]
    return client.iot_hub_resource.create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})


def iot_hub_route_update(cmd, client, hub_name, route_name, source_type=None, endpoint_name=None, enabled=None,
                         condition=None, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    updated_route = next((route for route in hub.properties.routing.routes
                          if route.name.lower() == route_name.lower()), None)
    if updated_route:
        updated_route.source = updated_route.source if source_type is None else source_type
        updated_route.endpoint_names = updated_route.endpoint_names if endpoint_name is None else endpoint_name.split()
        updated_route.condition = updated_route.condition if condition is None else condition
        updated_route.is_enabled = updated_route.is_enabled if enabled is None else enabled
    else:
        raise CLIError("No route found.")
    return client.iot_hub_resource.create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})


def iot_hub_route_test(cmd, client, hub_name, route_name=None, source_type=None, body=None, app_properties=None,
                       system_properties=None, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    route_message = RoutingMessage(
        body=body,
        app_properties=app_properties,
        system_properties=system_properties
    )

    if route_name:
        route = iot_hub_route_show(cmd, client, hub_name, route_name, resource_group_name)
        test_route_input = TestRouteInput(
            message=route_message,
            twin=None,
            route=route
        )
        return client.iot_hub_resource.test_route(test_route_input, hub_name, resource_group_name)
    test_all_routes_input = TestAllRoutesInput(
        routing_source=source_type,
        message=route_message,
        twin=None
    )
    return client.iot_hub_resource.test_all_routes(test_all_routes_input, hub_name, resource_group_name)


def iot_message_enrichment_create(cmd, client, hub_name, key, value, endpoints, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    if hub.properties.routing.enrichments is None:
        hub.properties.routing.enrichments = []
    hub.properties.routing.enrichments.append(EnrichmentProperties(key=key, value=value, endpoint_names=endpoints))
    return client.iot_hub_resource.create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})


def iot_message_enrichment_update(cmd, client, hub_name, key, value, endpoints, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    to_update = next((endpoint for endpoint in hub.properties.routing.enrichments if endpoint.key == key), None)
    if to_update:
        to_update.key = key
        to_update.value = value
        to_update.endpoint_names = endpoints
        return client.iot_hub_resource.create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})
    raise CLIError('No message enrichment with that key exists')


def iot_message_enrichment_delete(cmd, client, hub_name, key, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    to_remove = next((endpoint for endpoint in hub.properties.routing.enrichments if endpoint.key == key), None)
    if to_remove:
        hub.properties.routing.enrichments.remove(to_remove)
        return client.iot_hub_resource.create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})
    raise CLIError('No message enrichment with that key exists')


def iot_message_enrichment_list(cmd, client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    return hub.properties.routing.enrichments


def iot_hub_devicestream_show(cmd, client, hub_name, resource_group_name=None):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client, ResourceType
    resource_group_name = _ensure_resource_group_name(client, resource_group_name, hub_name)
    # DeviceStreams property is still in preview, so until GA we need to use an older API version (2019-07-01-preview)
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_IOTHUB, api_version='2019-07-01-preview')
    hub = client.iot_hub_resource.get(resource_group_name, hub_name)
    return hub.properties.device_streams


def iot_hub_manual_failover(cmd, client, hub_name, resource_group_name=None, no_wait=False):
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    resource_group_name = hub.additional_properties['resourcegroup']
    failover_region = next(x.location for x in hub.properties.locations if x.role.lower() == 'secondary')
    if no_wait:
        return client.iot_hub.manual_failover(hub_name, resource_group_name, failover_region)
    LongRunningOperation(cmd.cli_ctx)(client.iot_hub.manual_failover(hub_name, resource_group_name, failover_region))
    return iot_hub_get(cmd, client, hub_name, resource_group_name)


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


def _ensure_resource_group_existence(cli_ctx, resource_group_name):
    resource_group_client = resource_service_factory(cli_ctx).resource_groups
    return resource_group_client.check_existence(resource_group_name)


def _ensure_resource_group_name(client, resource_group_name, hub_name):
    if resource_group_name is None:
        return _get_iot_hub_by_name(client, hub_name).additional_properties['resourcegroup']
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
    hub_set = {h.name.lower() for h in hubs}
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


def _delete_routing_endpoints(endpoint_name, endpoint_type, endpoints):
    if endpoint_type:
        if EndpointType.ServiceBusQueue.value == endpoint_type.lower():
            endpoints.service_bus_queues = []
        elif EndpointType.ServiceBusTopic.value == endpoint_type.lower():
            endpoints.service_bus_topics = []
        elif EndpointType.AzureStorageContainer.value == endpoint_type.lower():
            endpoints.storage_containers = []
        elif EndpointType.EventHub.value == endpoint_type.lower():
            endpoints.event_hubs = []

    if endpoint_name:
        if any(e.name.lower() == endpoint_name.lower() for e in endpoints.service_bus_queues):
            sbq_endpoints = [e for e in endpoints.service_bus_queues if e.name.lower() != endpoint_name.lower()]
            endpoints.service_bus_queues = sbq_endpoints
        elif any(e.name.lower() == endpoint_name.lower() for e in endpoints.service_bus_topics):
            sbt_endpoints = [e for e in endpoints.service_bus_topics if e.name.lower() != endpoint_name.lower()]
            endpoints.service_bus_topics = sbt_endpoints
        elif any(e.name.lower() == endpoint_name.lower() for e in endpoints.storage_containers):
            sc_endpoints = [e for e in endpoints.storage_containers if e.name.lower() != endpoint_name.lower()]
            endpoints.storage_containers = sc_endpoints
        elif any(e.name.lower() == endpoint_name.lower() for e in endpoints.event_hubs):
            eh_endpoints = [e for e in endpoints.event_hubs if e.name.lower() != endpoint_name.lower()]
            endpoints.event_hubs = eh_endpoints

    if not endpoint_type and not endpoint_name:
        endpoints.service_bus_queues = []
        endpoints.service_bus_topics = []
        endpoints.storage_containers = []
        endpoints.event_hubs = []

    return endpoints


def iot_central_app_create(
        cmd, client, app_name, resource_group_name, subdomain, sku="ST2",
        location=None, template=None, display_name=None, no_wait=False
):
    cli_ctx = cmd.cli_ctx
    location = _ensure_location(cli_ctx, resource_group_name, location)
    display_name = _ensure_display_name(app_name, display_name)
    appSku = AppSkuInfo(name=sku)

    app = App(subdomain=subdomain,
              location=location,
              display_name=display_name,
              sku=appSku,
              template=template)

    return sdk_no_wait(no_wait, client.apps.create_or_update, resource_group_name, app_name, app)


def iot_central_app_get(client, app_name, resource_group_name=None):
    if resource_group_name is None:
        return _get_iot_central_app_by_name(client, app_name)
    return client.apps.get(resource_group_name, app_name)


def iot_central_app_delete(client, app_name, resource_group_name, no_wait=False):
    return sdk_no_wait(no_wait, client.apps.delete, resource_group_name, app_name)


def iot_central_app_list(client, resource_group_name=None):
    if resource_group_name is None:
        return client.apps.list_by_subscription()
    return client.apps.list_by_resource_group(resource_group_name)


def iot_central_app_update(client, app_name, parameters, resource_group_name):
    return client.apps.update(resource_group_name, app_name, parameters)


def _ensure_location(cli_ctx, resource_group_name, location):
    """Check to see if a location was provided. If not,
        fall back to the resource group location.
    :param object cli_ctx: CLI Context
    :param str resource_group_name: Resource group name
    :param str location: Location to create the resource
    """
    if location is None:
        resource_group_client = resource_service_factory(
            cli_ctx).resource_groups
        return resource_group_client.get(resource_group_name).location
    return location


def _ensure_display_name(app_name, display_name):
    if not display_name or display_name.isspace():
        return app_name
    return display_name


def _get_iot_central_app_by_name(client, app_name):
    """Search the current subscription for an app with the given name.
    :param object client: IoTCentralClient
    :param str app_name: App name to search for
    """
    all_apps = iot_central_app_list(client)
    if all_apps is None:
        raise CLIError(
            "No IoT Central application found in current subscription.")
    try:
        target_app = next(
            x for x in all_apps if app_name.lower() == x.name.lower())
    except StopIteration:
        raise CLIError(
            "No IoT Central application found with name {} in current subscription.".format(app_name))
    return target_app
