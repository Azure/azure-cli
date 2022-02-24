# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use,no-member,line-too-long,too-few-public-methods,too-many-lines,too-many-arguments,too-many-locals

import re
from enum import Enum
from knack.log import get_logger
from knack.util import CLIError
from msrestazure.azure_exceptions import CloudError
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    BadRequestError,
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
    ResourceNotFoundError,
    UnclassifiedUserFault
)
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.util import sdk_no_wait

from azure.mgmt.iothub.models import (IotHubSku,
                                      AccessRights,
                                      ArmIdentity,
                                      CertificateDescription,
                                      CertificateProperties,
                                      CertificateVerificationDescription,
                                      CloudToDeviceProperties,
                                      IotHubDescription,
                                      IotHubSkuInfo,
                                      SharedAccessSignatureAuthorizationRule,
                                      IotHubProperties,
                                      EventHubProperties,
                                      EventHubConsumerGroupBodyDescription,
                                      EventHubConsumerGroupName,
                                      FailoverInput,
                                      FeedbackProperties,
                                      ManagedIdentity,
                                      MessagingEndpointProperties,
                                      OperationInputs,
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


from azure.mgmt.iothubprovisioningservices.models import (CertificateBodyDescription,
                                                          ProvisioningServiceDescription,
                                                          IotDpsPropertiesDescription,
                                                          IotHubDefinitionDescription,
                                                          IotDpsSkuInfo,
                                                          IotDpsSku,
                                                          OperationInputs as DpsOperationInputs,
                                                          SharedAccessSignatureAuthorizationRuleAccessRightsDescription,
                                                          VerificationCodeRequest)


from azure.mgmt.iotcentral.models import (AppSkuInfo,
                                          App)
from azure.cli.command_modules.iot._constants import SYSTEM_ASSIGNED_IDENTITY
from azure.cli.command_modules.iot.shared import EndpointType, EncodingFormat, RenewKeyType, AuthenticationType, IdentityType
from ._client_factory import resource_service_factory
from ._client_factory import iot_hub_service_factory
from ._utils import open_certificate, generate_key


logger = get_logger(__name__)

# Identity types
SYSTEM_ASSIGNED = 'SystemAssigned'
NONE_IDENTITY = 'None'


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


def iot_dps_create(cmd, client, dps_name, resource_group_name, location=None, sku=IotDpsSku.s1.value, unit=1, tags=None, enable_data_residency=None):
    cli_ctx = cmd.cli_ctx
    _check_dps_name_availability(client.iot_dps_resource, dps_name)
    location = _ensure_location(cli_ctx, resource_group_name, location)
    dps_property = IotDpsPropertiesDescription(enable_data_residency=enable_data_residency)
    dps_description = ProvisioningServiceDescription(location=location,
                                                     properties=dps_property,
                                                     sku=IotDpsSkuInfo(name=sku, capacity=unit),
                                                     tags=tags)
    return client.iot_dps_resource.begin_create_or_update(resource_group_name, dps_name, dps_description)


def iot_dps_update(client, dps_name, parameters, resource_group_name=None, tags=None):
    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    if tags is not None:
        parameters.tags = tags
    return client.iot_dps_resource.begin_create_or_update(resource_group_name, dps_name, parameters)


def iot_dps_delete(client, dps_name, resource_group_name=None):
    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    return client.iot_dps_resource.begin_delete(dps_name, resource_group_name)


# DPS policy methods
def iot_dps_policy_list(client, dps_name, resource_group_name=None):
    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    return client.iot_dps_resource.list_keys(dps_name, resource_group_name)


def iot_dps_policy_get(client, dps_name, access_policy_name, resource_group_name=None):
    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    return client.iot_dps_resource.list_keys_for_key_name(dps_name, access_policy_name, resource_group_name)


def iot_dps_policy_create(
    cmd,
    client,
    dps_name,
    access_policy_name,
    rights,
    resource_group_name=None,
    primary_key=None,
    secondary_key=None,
    no_wait=False
):
    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    dps_access_policies = []
    dps_access_policies.extend(iot_dps_policy_list(client, dps_name, resource_group_name))
    if _does_policy_exist(dps_access_policies, access_policy_name):
        raise BadRequestError("Access policy {} already exists.".format(access_policy_name))

    dps = iot_dps_get(client, dps_name, resource_group_name)
    access_policy_rights = _convert_rights_to_access_rights(rights)
    dps_access_policies.append(SharedAccessSignatureAuthorizationRuleAccessRightsDescription(
        key_name=access_policy_name, rights=access_policy_rights, primary_key=primary_key, secondary_key=secondary_key))
    dps_property = IotDpsPropertiesDescription(iot_hubs=dps.properties.iot_hubs,
                                               allocation_policy=dps.properties.allocation_policy,
                                               authorization_policies=dps_access_policies)
    dps_description = ProvisioningServiceDescription(location=dps.location, properties=dps_property, sku=dps.sku)

    if no_wait:
        return client.iot_dps_resource.begin_create_or_update(resource_group_name, dps_name, dps_description)
    LongRunningOperation(cmd.cli_ctx)(client.iot_dps_resource.begin_create_or_update(resource_group_name, dps_name, dps_description))
    return iot_dps_policy_get(client, dps_name, access_policy_name, resource_group_name)


def iot_dps_policy_update(
    cmd,
    client,
    dps_name,
    access_policy_name,
    resource_group_name=None,
    primary_key=None,
    secondary_key=None,
    rights=None,
    no_wait=False
):
    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    dps_access_policies = []
    dps_access_policies.extend(iot_dps_policy_list(client, dps_name, resource_group_name))

    if not _does_policy_exist(dps_access_policies, access_policy_name):
        raise ResourceNotFoundError("Access policy {} doesn't exist.".format(access_policy_name))

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
        return client.iot_dps_resource.begin_create_or_update(resource_group_name, dps_name, dps_description)
    LongRunningOperation(cmd.cli_ctx)(client.iot_dps_resource.begin_create_or_update(resource_group_name, dps_name, dps_description))
    return iot_dps_policy_get(client, dps_name, access_policy_name, resource_group_name)


def iot_dps_policy_delete(cmd, client, dps_name, access_policy_name, resource_group_name=None, no_wait=False):
    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    dps_access_policies = []
    dps_access_policies.extend(iot_dps_policy_list(client, dps_name, resource_group_name))

    if not _does_policy_exist(dps_access_policies, access_policy_name):
        raise ResourceNotFoundError("Access policy {0} doesn't exist.".format(access_policy_name))
    updated_policies = [p for p in dps_access_policies if p.key_name.lower() != access_policy_name.lower()]

    dps = iot_dps_get(client, dps_name, resource_group_name)
    dps_property = IotDpsPropertiesDescription(iot_hubs=dps.properties.iot_hubs,
                                               allocation_policy=dps.properties.allocation_policy,
                                               authorization_policies=updated_policies)
    dps_description = ProvisioningServiceDescription(location=dps.location, properties=dps_property, sku=dps.sku)

    if no_wait:
        return client.iot_dps_resource.begin_create_or_update(resource_group_name, dps_name, dps_description)
    LongRunningOperation(cmd.cli_ctx)(client.iot_dps_resource.begin_create_or_update(resource_group_name, dps_name, dps_description))
    return iot_dps_policy_list(client, dps_name, resource_group_name)


# DPS linked hub methods
def iot_dps_linked_hub_list(client, dps_name, resource_group_name=None):
    dps = iot_dps_get(client, dps_name, resource_group_name)
    return dps.properties.iot_hubs


def iot_dps_linked_hub_get(cmd, client, dps_name, linked_hub, resource_group_name=None):
    if '.' not in linked_hub:
        hub_client = iot_hub_service_factory(cmd.cli_ctx)
        linked_hub = _get_iot_hub_hostname(hub_client, linked_hub)

    dps = iot_dps_get(client, dps_name, resource_group_name)
    for hub in dps.properties.iot_hubs:
        if hub.name == linked_hub:
            return hub
    raise ResourceNotFoundError("Linked hub '{0}' does not exist. Use 'iot dps linked-hub show to see all linked hubs.".format(linked_hub))


def iot_dps_linked_hub_create(
    cmd,
    client,
    dps_name,
    hub_name=None,
    hub_resource_group=None,
    connection_string=None,
    location=None,
    resource_group_name=None,
    apply_allocation_policy=None,
    allocation_weight=None,
    no_wait=False
):
    if not any([connection_string, hub_name]):
        raise RequiredArgumentMissingError("Please provide the IoT Hub name or connection string.")
    if not connection_string:
        # Get the connection string for the hub
        hub_client = iot_hub_service_factory(cmd.cli_ctx)
        connection_string = iot_hub_show_connection_string(
            hub_client, hub_name=hub_name, resource_group_name=hub_resource_group
        )['connectionString']

    if not location:
        # Parse out hub name from connection string if needed
        if not hub_name:
            try:
                hub_name = re.search(r"hostname=(.[^\;\.]+)?", connection_string, re.IGNORECASE).group(1)
            except AttributeError:
                raise InvalidArgumentValueError("Please provide a valid IoT Hub connection string.")

        hub_client = iot_hub_service_factory(cmd.cli_ctx)
        location = iot_hub_get(cmd, hub_client, hub_name=hub_name, resource_group_name=hub_resource_group).location

    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    dps_linked_hubs = []
    dps_linked_hubs.extend(iot_dps_linked_hub_list(client, dps_name, resource_group_name))

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
        return client.iot_dps_resource.begin_create_or_update(resource_group_name, dps_name, dps_description)
    LongRunningOperation(cmd.cli_ctx)(client.iot_dps_resource.begin_create_or_update(resource_group_name, dps_name, dps_description))
    return iot_dps_linked_hub_list(client, dps_name, resource_group_name)


def iot_dps_linked_hub_update(cmd, client, dps_name, linked_hub, resource_group_name=None, apply_allocation_policy=None,
                              allocation_weight=None, no_wait=False):
    if '.' not in linked_hub:
        hub_client = iot_hub_service_factory(cmd.cli_ctx)
        linked_hub = _get_iot_hub_hostname(hub_client, linked_hub)

    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    dps_linked_hubs = []
    dps_linked_hubs.extend(iot_dps_linked_hub_list(client, dps_name, resource_group_name))
    if not _is_linked_hub_existed(dps_linked_hubs, linked_hub):
        raise ResourceNotFoundError("Access policy {0} doesn't exist.".format(linked_hub))

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
        return client.iot_dps_resource.begin_create_or_update(resource_group_name, dps_name, dps_description)
    LongRunningOperation(cmd.cli_ctx)(client.iot_dps_resource.begin_create_or_update(resource_group_name, dps_name, dps_description))
    return iot_dps_linked_hub_get(cmd, client, dps_name, linked_hub, resource_group_name)


def iot_dps_linked_hub_delete(cmd, client, dps_name, linked_hub, resource_group_name=None, no_wait=False):
    if '.' not in linked_hub:
        hub_client = iot_hub_service_factory(cmd.cli_ctx)
        linked_hub = _get_iot_hub_hostname(hub_client, linked_hub)

    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    dps_linked_hubs = []
    dps_linked_hubs.extend(iot_dps_linked_hub_list(client, dps_name, resource_group_name))
    if not _is_linked_hub_existed(dps_linked_hubs, linked_hub):
        raise ResourceNotFoundError("Linked hub {0} doesn't exist.".format(linked_hub))
    updated_hub = [p for p in dps_linked_hubs if p.name.lower() != linked_hub.lower()]

    dps = iot_dps_get(client, dps_name, resource_group_name)
    dps_property = IotDpsPropertiesDescription(iot_hubs=updated_hub,
                                               allocation_policy=dps.properties.allocation_policy,
                                               authorization_policies=dps.properties.authorization_policies)
    dps_description = ProvisioningServiceDescription(location=dps.location, properties=dps_property, sku=dps.sku)

    if no_wait:
        return client.iot_dps_resource.begin_create_or_update(resource_group_name, dps_name, dps_description)
    LongRunningOperation(cmd.cli_ctx)(client.iot_dps_resource.begin_create_or_update(resource_group_name, dps_name, dps_description))
    return iot_dps_linked_hub_list(client, dps_name, resource_group_name)


# DPS certificate methods
def iot_dps_certificate_list(client, dps_name, resource_group_name=None):
    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    return client.dps_certificate.list(resource_group_name, dps_name)


def iot_dps_certificate_get(client, dps_name, certificate_name, resource_group_name=None):
    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    return client.dps_certificate.get(certificate_name, resource_group_name, dps_name)


def iot_dps_certificate_create(client, dps_name, certificate_name, certificate_path, resource_group_name=None, is_verified=None):
    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    cert_list = client.dps_certificate.list(resource_group_name, dps_name)
    for cert in cert_list.value:
        if cert.name == certificate_name:
            raise CLIError("Certificate '{0}' already exists. Use 'iot dps certificate update'"
                           " to update an existing certificate.".format(certificate_name))
    certificate = open_certificate(certificate_path)
    if not certificate:
        raise CLIError("Error uploading certificate '{0}'.".format(certificate_path))
    cert_description = CertificateBodyDescription(certificate=certificate, is_verified=is_verified)
    return client.dps_certificate.create_or_update(resource_group_name, dps_name, certificate_name, cert_description)


def iot_dps_certificate_update(client, dps_name, certificate_name, certificate_path, etag, resource_group_name=None, is_verified=None):
    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    cert_list = client.dps_certificate.list(resource_group_name, dps_name)
    for cert in cert_list.value:
        if cert.name == certificate_name:
            certificate = open_certificate(certificate_path)
            if not certificate:
                raise CLIError("Error uploading certificate '{0}'.".format(certificate_path))
            cert_description = CertificateBodyDescription(certificate=certificate, is_verified=is_verified)
            return client.dps_certificate.create_or_update(resource_group_name, dps_name, certificate_name, cert_description, etag)
    raise CLIError("Certificate '{0}' does not exist. Use 'iot dps certificate create' to create a new certificate."
                   .format(certificate_name))


def iot_dps_certificate_delete(client, dps_name, certificate_name, etag, resource_group_name=None):
    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    return client.dps_certificate.delete(resource_group_name, etag, dps_name, certificate_name)


def iot_dps_certificate_gen_code(client, dps_name, certificate_name, etag, resource_group_name=None):
    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    return client.dps_certificate.generate_verification_code(certificate_name, etag, resource_group_name, dps_name)


def iot_dps_certificate_verify(client, dps_name, certificate_name, certificate_path, etag, resource_group_name=None):
    resource_group_name = _ensure_dps_resource_group_name(client, resource_group_name, dps_name)
    certificate = open_certificate(certificate_path)
    if not certificate:
        raise CLIError("Error uploading certificate '{0}'.".format(certificate_path))
    request = VerificationCodeRequest(certificate=certificate)
    return client.dps_certificate.verify_certificate(certificate_name, etag, resource_group_name, dps_name, request)


# CUSTOM METHODS
def iot_hub_certificate_list(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    return client.certificates.list_by_iot_hub(resource_group_name, hub_name)


def iot_hub_certificate_get(client, hub_name, certificate_name, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    return client.certificates.get(resource_group_name, hub_name, certificate_name)


def iot_hub_certificate_create(client, hub_name, certificate_name, certificate_path, resource_group_name=None, is_verified=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    # Get list of certs
    cert_list = client.certificates.list_by_iot_hub(resource_group_name, hub_name)
    for cert in cert_list.value:
        if cert.name == certificate_name:
            raise CLIError("Certificate '{0}' already exists. Use 'iot hub certificate update'"
                           " to update an existing certificate.".format(certificate_name))
    certificate = open_certificate(certificate_path)
    if not certificate:
        raise CLIError("Error uploading certificate '{0}'.".format(certificate_path))
    cert_properties = CertificateProperties(certificate=certificate, is_verified=is_verified)
    cert_description = CertificateDescription(properties=cert_properties)
    return client.certificates.create_or_update(resource_group_name, hub_name, certificate_name, cert_description)


def iot_hub_certificate_update(client, hub_name, certificate_name, certificate_path, etag, resource_group_name=None, is_verified=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    cert_list = client.certificates.list_by_iot_hub(resource_group_name, hub_name)
    for cert in cert_list.value:
        if cert.name == certificate_name:
            certificate = open_certificate(certificate_path)
            if not certificate:
                raise CLIError("Error uploading certificate '{0}'.".format(certificate_path))
            cert_properties = CertificateProperties(certificate=certificate, is_verified=is_verified)
            cert_description = CertificateDescription(properties=cert_properties)
            return client.certificates.create_or_update(resource_group_name, hub_name, certificate_name, cert_description, etag)
    raise CLIError("Certificate '{0}' does not exist. Use 'iot hub certificate create' to create a new certificate."
                   .format(certificate_name))


def iot_hub_certificate_delete(client, hub_name, certificate_name, etag, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    return client.certificates.delete(resource_group_name, hub_name, certificate_name, etag)


def iot_hub_certificate_gen_code(client, hub_name, certificate_name, etag, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    return client.certificates.generate_verification_code(resource_group_name, hub_name, certificate_name, etag)


def iot_hub_certificate_verify(client, hub_name, certificate_name, certificate_path, etag, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    certificate = open_certificate(certificate_path)
    if not certificate:
        raise CLIError("Error uploading certificate '{0}'.".format(certificate_path))
    certificate_verify_body = CertificateVerificationDescription(certificate=certificate)
    return client.certificates.verify(resource_group_name, hub_name, certificate_name, etag, certificate_verify_body)


def iot_hub_create(cmd, client, hub_name, resource_group_name, location=None,
                   sku=IotHubSku.s1.value,
                   unit=1,
                   partition_count=4,
                   retention_day=1,
                   c2d_ttl=1,
                   c2d_max_delivery_count=10,
                   disable_local_auth=None,
                   disable_device_sas=None,
                   disable_module_sas=None,
                   enable_data_residency=None,
                   feedback_lock_duration=5,
                   feedback_ttl=1,
                   feedback_max_delivery_count=10,
                   enable_fileupload_notifications=False,
                   fileupload_notification_lock_duration=5,
                   fileupload_notification_max_delivery_count=10,
                   fileupload_notification_ttl=1,
                   fileupload_storage_connectionstring=None,
                   fileupload_storage_container_name=None,
                   fileupload_sas_ttl=1,
                   fileupload_storage_authentication_type=None,
                   fileupload_storage_container_uri=None,
                   fileupload_storage_identity=None,
                   min_tls_version=None,
                   tags=None,
                   system_identity=None,
                   user_identities=None,
                   identity_role=None,
                   identity_scopes=None):
    from datetime import timedelta
    cli_ctx = cmd.cli_ctx
    if enable_fileupload_notifications:
        if not fileupload_storage_connectionstring or not fileupload_storage_container_name:
            raise RequiredArgumentMissingError('Please specify storage endpoint (storage connection string and storage container name).')
    if fileupload_storage_connectionstring and not fileupload_storage_container_name:
        raise RequiredArgumentMissingError('Please mention storage container name.')
    if fileupload_storage_container_name and not fileupload_storage_connectionstring:
        raise RequiredArgumentMissingError('Please mention storage connection string.')
    identity_based_file_upload = fileupload_storage_authentication_type and fileupload_storage_authentication_type == AuthenticationType.IdentityBased.value
    if not identity_based_file_upload and fileupload_storage_identity:
        raise RequiredArgumentMissingError('In order to set a fileupload storage identity, please set file upload storage authentication (--fsa) to IdentityBased')
    if identity_based_file_upload or fileupload_storage_identity:
        # Not explicitly setting fileupload_storage_identity assumes system-assigned managed identity for file upload
        if fileupload_storage_identity in [None, SYSTEM_ASSIGNED_IDENTITY] and not system_identity:
            raise ArgumentUsageError('System managed identity [--mi-system-assigned] must be enabled in order to use managed identity for file upload')
        if fileupload_storage_identity and fileupload_storage_identity != SYSTEM_ASSIGNED_IDENTITY and not user_identities:
            raise ArgumentUsageError('User identity [--mi-user-assigned] must be added in order to use it for file upload')
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
                                                                        ttl_as_iso8601=timedelta(hours=fileupload_notification_ttl),
                                                                        lock_duration_as_iso8601=timedelta(seconds=fileupload_notification_lock_duration))
    storage_endpoint_dic = {}
    storage_endpoint_dic['$default'] = StorageEndpointProperties(
        sas_ttl_as_iso8601=timedelta(hours=fileupload_sas_ttl),
        connection_string=fileupload_storage_connectionstring if fileupload_storage_connectionstring else '',
        container_name=fileupload_storage_container_name if fileupload_storage_container_name else '',
        authentication_type=fileupload_storage_authentication_type if fileupload_storage_authentication_type else None,
        container_uri=fileupload_storage_container_uri if fileupload_storage_container_uri else '',
        identity=ManagedIdentity(user_assigned_identity=fileupload_storage_identity) if fileupload_storage_identity else None)

    properties = IotHubProperties(event_hub_endpoints=event_hub_dic,
                                  messaging_endpoints=msg_endpoint_dic,
                                  storage_endpoints=storage_endpoint_dic,
                                  cloud_to_device=cloud_to_device_properties,
                                  min_tls_version=min_tls_version,
                                  enable_data_residency=enable_data_residency,
                                  disable_local_auth=disable_local_auth,
                                  disable_device_sas=disable_device_sas,
                                  disable_module_sas=disable_module_sas)
    properties.enable_file_upload_notifications = enable_fileupload_notifications

    hub_description = IotHubDescription(location=location,
                                        sku=sku,
                                        properties=properties,
                                        tags=tags)
    if (system_identity or user_identities):
        hub_description.identity = _build_identity(system=bool(system_identity), identities=user_identities)
    if bool(identity_role) ^ bool(identity_scopes):
        raise RequiredArgumentMissingError('At least one scope (--scopes) and one role (--role) required for system-assigned managed identity role assignment')

    def identity_assignment(lro):
        try:
            from azure.cli.core.commands.arm import assign_identity
            instance = lro.resource().as_dict()
            identity = instance.get("identity")
            if identity:
                principal_id = identity.get("principal_id")
                if principal_id:
                    hub_description.identity.principal_id = principal_id
                    for scope in identity_scopes:
                        assign_identity(cmd.cli_ctx, lambda: hub_description, lambda hub: hub_description, identity_role=identity_role, identity_scope=scope)
        except CloudError as e:
            raise e

    create = client.iot_hub_resource.begin_create_or_update(resource_group_name, hub_name, hub_description, polling=True)
    if identity_role and identity_scopes:
        create.add_done_callback(identity_assignment)
    return create


def iot_hub_get(cmd, client, hub_name, resource_group_name=None):
    cli_ctx = cmd.cli_ctx
    if resource_group_name is None:
        return _get_iot_hub_by_name(client, hub_name)
    if not _ensure_resource_group_existence(cli_ctx, resource_group_name):
        raise CLIError("Resource group '{0}' could not be found.".format(resource_group_name))
    name_availability = client.iot_hub_resource.check_name_availability(OperationInputs(name=hub_name))
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
                          disable_local_auth=None,
                          disable_device_sas=None,
                          disable_module_sas=None,
                          feedback_lock_duration=None,
                          feedback_ttl=None,
                          feedback_max_delivery_count=None,
                          enable_fileupload_notifications=None,
                          fileupload_notification_lock_duration=None,
                          fileupload_notification_max_delivery_count=None,
                          fileupload_notification_ttl=None,
                          fileupload_storage_connectionstring=None,
                          fileupload_storage_container_name=None,
                          fileupload_sas_ttl=None,
                          fileupload_storage_authentication_type=None,
                          fileupload_storage_container_uri=None,
                          fileupload_storage_identity=None,
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
    if fileupload_notification_lock_duration is not None:
        lock_duration = timedelta(seconds=fileupload_notification_lock_duration)
        instance.properties.messaging_endpoints['fileNotifications'].lock_duration_as_iso8601 = lock_duration
    if fileupload_notification_max_delivery_count is not None:
        count = fileupload_notification_max_delivery_count
        instance.properties.messaging_endpoints['fileNotifications'].max_delivery_count = count
    if fileupload_notification_ttl is not None:
        ttl = timedelta(hours=fileupload_notification_ttl)
        instance.properties.messaging_endpoints['fileNotifications'].ttl_as_iso8601 = ttl
    # only bother with $default storage endpoint checking if modifying fileupload params
    if any([
            fileupload_storage_connectionstring, fileupload_storage_container_name, fileupload_sas_ttl,
            fileupload_storage_authentication_type, fileupload_storage_container_uri, fileupload_storage_identity]):
        default_storage_endpoint = instance.properties.storage_endpoints.get('$default', None)
        # no default storage endpoint, either recreate with existing params or throw an error
        if not default_storage_endpoint:
            if not all([fileupload_storage_connectionstring, fileupload_storage_container_name]):
                raise UnclassifiedUserFault('This hub has no default storage endpoint for file upload.\n'
                                            'Please recreate your default storage endpoint by running '
                                            '`az iot hub update --name {hub_name} --fcs {storage_connection_string} --fc {storage_container_name}`')
            default_storage_endpoint = StorageEndpointProperties(container_name=fileupload_storage_container_name, connection_string=fileupload_storage_connectionstring)

        # if setting a fileupload storage identity or changing fileupload to identity-based
        if fileupload_storage_identity or fileupload_storage_authentication_type == AuthenticationType.IdentityBased.value:
            _validate_fileupload_identity(instance, fileupload_storage_identity)

        instance.properties.storage_endpoints['$default'] = _process_fileupload_args(
            default_storage_endpoint,
            fileupload_storage_connectionstring,
            fileupload_storage_container_name,
            fileupload_sas_ttl,
            fileupload_storage_authentication_type,
            fileupload_storage_container_uri,
            fileupload_storage_identity,
        )

    # sas token authentication switches
    if disable_local_auth is not None:
        instance.properties.disable_local_auth = disable_local_auth
    if disable_device_sas is not None:
        instance.properties.disable_device_sas = disable_device_sas
    if disable_module_sas is not None:
        instance.properties.disable_module_sas = disable_module_sas

    return instance


def iot_hub_update(client, hub_name, parameters, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.begin_create_or_update(resource_group_name, hub_name, parameters, {'IF-MATCH': parameters.etag}, polling=True)


def iot_hub_delete(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.begin_delete(resource_group_name, hub_name, polling=True)


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
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    conn_str = _get_hub_connection_string(client, hub_name, resource_group_name, policy_name, key_type, show_all)
    return {'connectionString': conn_str if show_all else conn_str[0]}


def _get_hub_connection_string(client, hub_name, resource_group_name, policy_name, key_type, show_all):
    policies = []
    if show_all:
        policies.extend(iot_hub_policy_list(client, hub_name, resource_group_name))
    else:
        policies.append(iot_hub_policy_get(client, hub_name, policy_name, resource_group_name))
    hostname = _get_iot_hub_hostname(client, hub_name)
    conn_str_template = 'HostName={};SharedAccessKeyName={};SharedAccessKey={}'
    return [conn_str_template.format(hostname,
                                     p.key_name,
                                     p.secondary_key if key_type == KeyType.secondary else p.primary_key) for p in policies]


def iot_hub_sku_list(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.get_valid_skus(resource_group_name, hub_name)


def iot_hub_consumer_group_create(client, hub_name, consumer_group_name, resource_group_name=None, event_hub_name='events'):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    consumer_group_body = EventHubConsumerGroupBodyDescription(properties=EventHubConsumerGroupName(name=consumer_group_name))
    # Fix for breaking change argument in track 1 SDK method.
    from azure.cli.core.util import get_arg_list
    create_cg_op = client.iot_hub_resource.create_event_hub_consumer_group
    if "consumer_group_body" not in get_arg_list(create_cg_op):
        return create_cg_op(resource_group_name, hub_name, event_hub_name, consumer_group_name)
    return create_cg_op(resource_group_name, hub_name, event_hub_name, consumer_group_name, consumer_group_body=consumer_group_body)


def iot_hub_consumer_group_list(client, hub_name, resource_group_name=None, event_hub_name='events'):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.list_event_hub_consumer_groups(resource_group_name, hub_name, event_hub_name)


def iot_hub_consumer_group_get(client, hub_name, consumer_group_name, resource_group_name=None, event_hub_name='events'):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.get_event_hub_consumer_group(resource_group_name, hub_name, event_hub_name, consumer_group_name)


def iot_hub_consumer_group_delete(client, hub_name, consumer_group_name, resource_group_name=None, event_hub_name='events'):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.delete_event_hub_consumer_group(resource_group_name, hub_name, event_hub_name, consumer_group_name)


def iot_hub_identity_assign(cmd, client, hub_name, system_identity=None, user_identities=None, identity_role=None, identity_scopes=None, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)

    def getter():
        return iot_hub_get(cmd, client, hub_name, resource_group_name)

    def setter(hub):

        if user_identities and not hub.identity.user_assigned_identities:
            hub.identity.user_assigned_identities = {}
        if user_identities:
            for identity in user_identities:
                hub.identity.user_assigned_identities[identity] = hub.identity.user_assigned_identities.get(identity, {}) if hub.identity.user_assigned_identities else {}

        has_system_identity = hub.identity.type in [IdentityType.system_assigned_user_assigned.value, IdentityType.system_assigned.value]

        if system_identity or has_system_identity:
            hub.identity.type = IdentityType.system_assigned_user_assigned.value if hub.identity.user_assigned_identities else IdentityType.system_assigned.value
        else:
            hub.identity.type = IdentityType.user_assigned.value if hub.identity.user_assigned_identities else IdentityType.none.value

        poller = client.iot_hub_resource.begin_create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})
        return LongRunningOperation(cmd.cli_ctx)(poller)

    if bool(identity_role) ^ bool(identity_scopes):
        raise RequiredArgumentMissingError('At least one scope (--scopes) and one role (--role) required for system-managed identity role assignment.')
    if not system_identity and not user_identities:
        raise RequiredArgumentMissingError('No identities provided to assign. Please provide system (--system) or user-assigned identities (--user).')
    if identity_role and identity_scopes:
        from azure.cli.core.commands.arm import assign_identity
        for scope in identity_scopes:
            hub = assign_identity(cmd.cli_ctx, getter, setter, identity_role=identity_role, identity_scope=scope)
        return hub.identity
    result = setter(getter())
    return result.identity


def iot_hub_identity_show(cmd, client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    return hub.identity


def iot_hub_identity_remove(cmd, client, hub_name, system_identity=None, user_identities=None, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    hub_identity = hub.identity

    if not system_identity and user_identities is None:
        raise RequiredArgumentMissingError('No identities provided to remove. Please provide system (--system) or user-assigned identities (--user).')
    # Turn off system managed identity
    if system_identity:
        if hub_identity.type not in [
                IdentityType.system_assigned.value,
                IdentityType.system_assigned_user_assigned.value
        ]:
            raise ArgumentUsageError('Hub {} is not currently using a system-assigned identity'.format(hub_name))
        hub_identity.type = IdentityType.user_assigned if hub.identity.type in [IdentityType.user_assigned.value, IdentityType.system_assigned_user_assigned.value] else IdentityType.none.value

    if user_identities:
        # loop through user_identities to remove
        for identity in user_identities:
            if not hub_identity.user_assigned_identities[identity]:
                raise ArgumentUsageError('Hub {0} is not currently using a user-assigned identity with id: {1}'.format(hub_name, identity))
            del hub_identity.user_assigned_identities[identity]
        if not hub_identity.user_assigned_identities:
            del hub_identity.user_assigned_identities
    elif isinstance(user_identities, list):
        del hub_identity.user_assigned_identities

    if hub_identity.type in [
            IdentityType.system_assigned.value,
            IdentityType.system_assigned_user_assigned.value
    ]:
        hub_identity.type = IdentityType.system_assigned_user_assigned.value if getattr(hub_identity, 'user_assigned_identities', None) else IdentityType.system_assigned.value
    else:
        hub_identity.type = IdentityType.user_assigned.value if getattr(hub_identity, 'user_assigned_identities', None) else IdentityType.none.value

    hub.identity = hub_identity
    if not getattr(hub.identity, 'user_assigned_identities', None):
        hub.identity.user_assigned_identities = None
    poller = client.iot_hub_resource.begin_create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})
    lro = LongRunningOperation(cmd.cli_ctx)(poller)
    return lro.identity


def iot_hub_policy_list(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.list_keys(resource_group_name, hub_name)


def iot_hub_policy_get(client, hub_name, policy_name, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.get_keys_for_key_name(resource_group_name, hub_name, policy_name)


def iot_hub_policy_create(cmd, client, hub_name, policy_name, permissions, resource_group_name=None):
    rights = _convert_perms_to_access_rights(permissions)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    policies = []
    policies.extend(iot_hub_policy_list(client, hub_name, hub.additional_properties['resourcegroup']))
    if _does_policy_exist(policies, policy_name):
        raise CLIError("Policy {0} already existed.".format(policy_name))
    policies.append(SharedAccessSignatureAuthorizationRule(key_name=policy_name, rights=rights))
    hub.properties.authorization_policies = policies
    return client.iot_hub_resource.begin_create_or_update(hub.additional_properties['resourcegroup'], hub_name, hub, {'IF-MATCH': hub.etag})


def iot_hub_policy_delete(cmd, client, hub_name, policy_name, resource_group_name=None):
    import copy
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    policies = iot_hub_policy_list(client, hub_name, hub.additional_properties['resourcegroup'])
    if not _does_policy_exist(copy.deepcopy(policies), policy_name):
        raise CLIError("Policy {0} not found.".format(policy_name))
    updated_policies = [p for p in policies if p.key_name.lower() != policy_name.lower()]
    hub.properties.authorization_policies = updated_policies
    return client.iot_hub_resource.begin_create_or_update(hub.additional_properties['resourcegroup'], hub_name, hub, {'IF-MATCH': hub.etag})


def iot_hub_policy_key_renew(cmd, client, hub_name, policy_name, regenerate_key, resource_group_name=None, no_wait=False):
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    policies = []
    policies.extend(iot_hub_policy_list(client, hub_name, hub.additional_properties['resourcegroup']))
    if not _does_policy_exist(policies, policy_name):
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
        return client.iot_hub_resource.begin_create_or_update(hub.additional_properties['resourcegroup'], hub_name, hub, {'IF-MATCH': hub.etag})
    LongRunningOperation(cmd.cli_ctx)(client.iot_hub_resource.begin_create_or_update(hub.additional_properties['resourcegroup'], hub_name, hub, {'IF-MATCH': hub.etag}))
    return iot_hub_policy_get(client, hub_name, policy_name, resource_group_name)


def _does_policy_exist(policies, policy_name):
    policy_set = {p.key_name.lower() for p in policies}
    return policy_name.lower() in policy_set


def iot_hub_get_quota_metrics(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    iotHubQuotaMetricCollection = []
    iotHubQuotaMetricCollection.extend(client.iot_hub_resource.get_quota_metrics(resource_group_name, hub_name))
    for quotaMetric in iotHubQuotaMetricCollection:
        if quotaMetric.name == 'TotalDeviceCount':
            quotaMetric.max_value = 'Unlimited'
    return iotHubQuotaMetricCollection


def iot_hub_get_stats(client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    return client.iot_hub_resource.get_stats(resource_group_name, hub_name)


def validate_authentication_type_input(endpoint_type, connection_string=None, authentication_type=None, endpoint_uri=None, entity_path=None):
    is_keyBased = (AuthenticationType.KeyBased.value == authentication_type) or (authentication_type is None)
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
                                    authentication_type=None, endpoint_uri=None, entity_path=None,
                                    identity=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    if identity and authentication_type != AuthenticationType.IdentityBased.value:
        raise ArgumentUsageError("In order to use an identity for authentication, you must select --auth-type as 'identityBased'")

    if EndpointType.EventHub.value == endpoint_type.lower():
        hub.properties.routing.endpoints.event_hubs.append(
            RoutingEventHubProperties(
                connection_string=connection_string,
                name=endpoint_name,
                subscription_id=endpoint_subscription_id,
                resource_group=endpoint_resource_group,
                authentication_type=authentication_type,
                endpoint_uri=endpoint_uri,
                entity_path=entity_path,
                identity=ManagedIdentity(user_assigned_identity=identity) if identity and identity not in [IdentityType.none.value, SYSTEM_ASSIGNED_IDENTITY] else None
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
                entity_path=entity_path,
                identity=ManagedIdentity(user_assigned_identity=identity) if identity and identity not in [IdentityType.none.value, SYSTEM_ASSIGNED_IDENTITY] else None
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
                entity_path=entity_path,
                identity=ManagedIdentity(user_assigned_identity=identity) if identity and identity not in [IdentityType.none.value, SYSTEM_ASSIGNED_IDENTITY] else None
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
                endpoint_uri=endpoint_uri,
                identity=ManagedIdentity(user_assigned_identity=identity) if identity and identity not in [IdentityType.none.value, SYSTEM_ASSIGNED_IDENTITY] else None
            )
        )

    return client.iot_hub_resource.begin_create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})


def iot_hub_routing_endpoint_list(cmd, client, hub_name, endpoint_type=None, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
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
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
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
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    hub.properties.routing.endpoints = _delete_routing_endpoints(endpoint_name, endpoint_type, hub.properties.routing.endpoints)
    return client.iot_hub_resource.begin_create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})


def iot_hub_route_create(cmd, client, hub_name, route_name, source_type, endpoint_name, enabled=None, condition=None,
                         resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
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
    return client.iot_hub_resource.begin_create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})


def iot_hub_route_list(cmd, client, hub_name, source_type=None, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    if source_type:
        return [route for route in hub.properties.routing.routes if route.source.lower() == source_type.lower()]
    return hub.properties.routing.routes


def iot_hub_route_show(cmd, client, hub_name, route_name, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    for route in hub.properties.routing.routes:
        if route.name.lower() == route_name.lower():
            return route
    raise CLIError("No route found.")


def iot_hub_route_delete(cmd, client, hub_name, route_name=None, source_type=None, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    if not route_name and not source_type:
        hub.properties.routing.routes = []
    if route_name:
        hub.properties.routing.routes = [route for route in hub.properties.routing.routes
                                         if route.name.lower() != route_name.lower()]
    if source_type:
        hub.properties.routing.routes = [route for route in hub.properties.routing.routes
                                         if route.source.lower() != source_type.lower()]
    return client.iot_hub_resource.begin_create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})


def iot_hub_route_update(cmd, client, hub_name, route_name, source_type=None, endpoint_name=None, enabled=None,
                         condition=None, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
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
    return client.iot_hub_resource.begin_create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})


def iot_hub_route_test(cmd, client, hub_name, route_name=None, source_type=None, body=None, app_properties=None,
                       system_properties=None, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
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
        return client.iot_hub_resource.test_route(hub_name, resource_group_name, test_route_input)
    test_all_routes_input = TestAllRoutesInput(
        routing_source=source_type,
        message=route_message,
        twin=None
    )
    return client.iot_hub_resource.test_all_routes(hub_name, resource_group_name, test_all_routes_input)


def iot_message_enrichment_create(cmd, client, hub_name, key, value, endpoints, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    if hub.properties.routing.enrichments is None:
        hub.properties.routing.enrichments = []
    hub.properties.routing.enrichments.append(EnrichmentProperties(key=key, value=value, endpoint_names=endpoints))
    return client.iot_hub_resource.begin_create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})


def iot_message_enrichment_update(cmd, client, hub_name, key, value, endpoints, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    to_update = next((endpoint for endpoint in hub.properties.routing.enrichments if endpoint.key == key), None)
    if to_update:
        to_update.key = key
        to_update.value = value
        to_update.endpoint_names = endpoints
        return client.iot_hub_resource.begin_create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})
    raise CLIError('No message enrichment with that key exists')


def iot_message_enrichment_delete(cmd, client, hub_name, key, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    to_remove = next((endpoint for endpoint in hub.properties.routing.enrichments if endpoint.key == key), None)
    if to_remove:
        hub.properties.routing.enrichments.remove(to_remove)
        return client.iot_hub_resource.begin_create_or_update(resource_group_name, hub_name, hub, {'IF-MATCH': hub.etag})
    raise CLIError('No message enrichment with that key exists')


def iot_message_enrichment_list(cmd, client, hub_name, resource_group_name=None):
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    return hub.properties.routing.enrichments


def iot_hub_devicestream_show(cmd, client, hub_name, resource_group_name=None):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client, ResourceType
    resource_group_name = _ensure_hub_resource_group_name(client, resource_group_name, hub_name)
    # DeviceStreams property is still in preview, so until GA we need to use a preview API-version
    client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_IOTHUB, api_version='2019-07-01-preview')
    hub = client.iot_hub_resource.get(resource_group_name, hub_name)
    return hub.properties.device_streams


def iot_hub_manual_failover(cmd, client, hub_name, resource_group_name=None, no_wait=False):
    hub = iot_hub_get(cmd, client, hub_name, resource_group_name)
    resource_group_name = hub.additional_properties['resourcegroup']
    failover_region = next(x.location for x in hub.properties.locations if x.role.lower() == 'secondary')
    failover_input = FailoverInput(failover_region=failover_region)
    if no_wait:
        return client.iot_hub.begin_manual_failover(hub_name, resource_group_name, failover_input)
    LongRunningOperation(cmd.cli_ctx)(client.iot_hub.begin_manual_failover(hub_name, resource_group_name, failover_input))
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


def _get_iot_hub_hostname(client, hub_name):
    # Intermediate fix to support domains beyond azure-devices.net properly
    hub = _get_iot_hub_by_name(client, hub_name)
    return hub.properties.host_name


def _ensure_resource_group_existence(cli_ctx, resource_group_name):
    resource_group_client = resource_service_factory(cli_ctx).resource_groups
    return resource_group_client.check_existence(resource_group_name)


def _ensure_hub_resource_group_name(client, resource_group_name, hub_name):
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


def _ensure_dps_resource_group_name(client, resource_group_name, dps_name):
    if resource_group_name is None:
        return _get_iot_dps_by_name(client, dps_name).additional_properties['resourcegroup']
    return resource_group_name


def _check_dps_name_availability(iot_dps_resource, dps_name):
    name_availability = iot_dps_resource.check_provisioning_service_name_availability(DpsOperationInputs(name=dps_name))
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
        location=None, template=None, display_name=None, no_wait=False, mi_system_assigned=False
):
    cli_ctx = cmd.cli_ctx
    location = _ensure_location(cli_ctx, resource_group_name, location)
    display_name = _ensure_display_name(app_name, display_name)
    appSku = AppSkuInfo(name=sku)
    appid = {"type": "SystemAssigned"} if mi_system_assigned else None

    app = App(subdomain=subdomain,
              location=location,
              display_name=display_name,
              sku=appSku,
              template=template,
              identity=appid)

    return sdk_no_wait(no_wait, client.apps.begin_create_or_update, resource_group_name, app_name, app)


def iot_central_app_get(client, app_name, resource_group_name=None):
    if resource_group_name is None:
        return _get_iot_central_app_by_name(client, app_name)
    return client.apps.get(resource_group_name, app_name)


def iot_central_app_delete(client, app_name, resource_group_name, no_wait=False):
    return sdk_no_wait(no_wait, client.apps.begin_delete, resource_group_name, app_name)


def iot_central_app_list(client, resource_group_name=None):
    if resource_group_name is None:
        return client.apps.list_by_subscription()
    return client.apps.list_by_resource_group(resource_group_name)


def iot_central_app_update(client, app_name, parameters, resource_group_name):
    return client.apps.begin_update(resource_group_name, app_name, parameters)


def iot_central_app_assign_identity(client, app_name, system_assigned=False, resource_group_name=None):
    app = iot_central_app_get(client, app_name, resource_group_name)

    if system_assigned:
        app.identity.type = SYSTEM_ASSIGNED

    poller = iot_central_app_update(client, app_name, app, resource_group_name)
    return poller.result().identity


def iot_central_app_remove_identity(client, app_name, system_assigned=False, resource_group_name=None):
    app = iot_central_app_get(client, app_name, resource_group_name)

    if system_assigned and (app.identity.type.upper() == SYSTEM_ASSIGNED.upper()):
        app.identity.type = NONE_IDENTITY

    poller = iot_central_app_update(client, app_name, app, resource_group_name)
    return poller.result().identity


def iot_central_app_show_identity(client, app_name, resource_group_name=None):
    app = iot_central_app_get(client, app_name, resource_group_name)
    return app.identity


def _ensure_location(cli_ctx, resource_group_name, location):
    """Check to see if a location was provided. If not,
        fall back to the resource group location.
    :param object cli_ctx: CLI Context
    :param str resource_group_name: Resource group name
    :param str location: Location to create the resource
    """
    if location is None:
        resource_group_client = resource_service_factory(cli_ctx).resource_groups
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


def _process_fileupload_args(
        default_storage_endpoint,
        fileupload_storage_connectionstring=None,
        fileupload_storage_container_name=None,
        fileupload_sas_ttl=None,
        fileupload_storage_authentication_type=None,
        fileupload_storage_container_uri=None,
        fileupload_storage_identity=None,
):
    from datetime import timedelta
    if fileupload_storage_authentication_type and fileupload_storage_authentication_type == AuthenticationType.IdentityBased.value:
        default_storage_endpoint.authentication_type = AuthenticationType.IdentityBased.value
        if fileupload_storage_container_uri:
            default_storage_endpoint.container_uri = fileupload_storage_container_uri
    elif fileupload_storage_authentication_type and fileupload_storage_authentication_type == AuthenticationType.KeyBased.value:
        default_storage_endpoint.authentication_type = AuthenticationType.KeyBased.value
        default_storage_endpoint.identity = None
    elif fileupload_storage_authentication_type is not None:
        default_storage_endpoint.authentication_type = None
        default_storage_endpoint.container_uri = None
    # TODO - remove connection string and set containerURI once fileUpload SAS URL is enabled
    if fileupload_storage_connectionstring is not None and fileupload_storage_container_name is not None:
        default_storage_endpoint.connection_string = fileupload_storage_connectionstring
        default_storage_endpoint.container_name = fileupload_storage_container_name
    elif fileupload_storage_connectionstring is not None:
        raise RequiredArgumentMissingError('Please mention storage container name.')
    elif fileupload_storage_container_name is not None:
        raise RequiredArgumentMissingError('Please mention storage connection string.')
    if fileupload_sas_ttl is not None:
        default_storage_endpoint.sas_ttl_as_iso8601 = timedelta(hours=fileupload_sas_ttl)

    # Fix for identity/authentication-type params missing on hybrid profile api
    if hasattr(default_storage_endpoint, 'authentication_type'):
        # If we are now (or will be) using fsa=identity AND we've set a new identity
        if default_storage_endpoint.authentication_type == AuthenticationType.IdentityBased.value and fileupload_storage_identity:
            # setup new fsi
            default_storage_endpoint.identity = ManagedIdentity(
                user_assigned_identity=fileupload_storage_identity) if fileupload_storage_identity not in [IdentityType.none.value, SYSTEM_ASSIGNED_IDENTITY] else None
        # otherwise - let them know they need identity-based auth enabled
        elif fileupload_storage_identity:
            raise ArgumentUsageError('In order to set a file upload storage identity, you must set the file upload storage authentication type (--fsa) to IdentityBased')

    return default_storage_endpoint


def _validate_fileupload_identity(instance, fileupload_storage_identity):
    instance_identity = _get_hub_identity_type(instance)

    # if hub has no identity
    if not instance_identity or instance_identity == IdentityType.none.value:
        raise ArgumentUsageError('Hub has no identity assigned, please assign a system or user-assigned managed identity to use for file-upload with `az iot hub identity assign`')

    has_system_identity = instance_identity in [IdentityType.system_assigned.value, IdentityType.system_assigned_user_assigned.value]
    has_user_identity = instance_identity in [IdentityType.user_assigned.value, IdentityType.system_assigned_user_assigned.value]

    # if changing storage identity to '[system]'
    if fileupload_storage_identity in [None, SYSTEM_ASSIGNED_IDENTITY]:
        if not has_system_identity:
            raise ArgumentUsageError('System managed identity must be enabled in order to use managed identity for file upload')
    # if changing to user identity and hub has no user identities
    elif fileupload_storage_identity and not has_user_identity:
        raise ArgumentUsageError('User identity {} must be added to hub in order to use it for file upload'.format(fileupload_storage_identity))


def _get_hub_identity_type(instance):
    identity = getattr(instance, 'identity', {})
    return getattr(identity, 'type', None)


def _build_identity(system=False, identities=None):
    identity_type = IdentityType.none.value
    if not (system or identities):
        return ArmIdentity(type=identity_type)
    if system:
        identity_type = IdentityType.system_assigned.value
    user_identities = list(identities) if identities else None
    if user_identities and identity_type == IdentityType.system_assigned.value:
        identity_type = IdentityType.system_assigned_user_assigned.value
    elif user_identities:
        identity_type = IdentityType.user_assigned.value

    identity = ArmIdentity(type=identity_type)
    if user_identities:
        identity.user_assigned_identities = {i: {} for i in user_identities}  # pylint: disable=not-an-iterable

    return identity
