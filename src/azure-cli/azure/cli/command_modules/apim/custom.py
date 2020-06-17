# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.util import sdk_no_wait
from azure.mgmt.apimanagement.models import (ApiManagementServiceResource, ApiManagementServiceIdentity,
                                             ApiManagementServiceSkuProperties, ApiManagementServiceBackupRestoreParameters,
                                             ApiContract, ApiType, Protocol,
                                             VirtualNetworkType, SkuType)

# Service Operations


def create_apim(client, resource_group_name, name, publisher_email, sku_name=SkuType.developer.value,
                sku_capacity=1, virtual_network_type=VirtualNetworkType.none.value, enable_managed_identity=False,
                enable_client_certificate=None, publisher_name=None, location=None, tags=None, no_wait=False):

    resource = ApiManagementServiceResource(
        location=location,
        notification_sender_email=publisher_email,
        publisher_email=publisher_email,
        publisher_name=publisher_name,
        sku=ApiManagementServiceSkuProperties(name=sku_name, capacity=sku_capacity),
        enable_client_certificate=enable_client_certificate,
        virtual_network_type=VirtualNetworkType(virtual_network_type),
        tags=tags
    )

    if enable_managed_identity:
        resource['identity'] = ApiManagementServiceIdentity(type="SystemAssigned")

    if resource.sku.name == SkuType.consumption.value:
        resource.sku.capacity = None

    cms = client.api_management_service

    return sdk_no_wait(no_wait, cms.create_or_update,
                       resource_group_name=resource_group_name,
                       service_name=name, parameters=resource)


def update_apim(instance, publisher_email=None, sku_name=None, sku_capacity=None,
                virtual_network_type=None, publisher_name=None, enable_managed_identity=None,
                enable_client_certificate=None, tags=None):

    if publisher_email is not None:
        instance.publisher_email = publisher_email

    if sku_name is not None:
        instance.sku.name = sku_name

    if sku_capacity is not None:
        instance.sku.capacity = sku_capacity

    if virtual_network_type is not None:
        instance.virtual_network_type = virtual_network_type

    if publisher_email is not None:
        instance.publisher_email = publisher_email

    if publisher_name is not None:
        instance.publisher_name = publisher_name

    if not enable_managed_identity:
        instance.identity = None
    else:
        if instance.identity is None:
            instance.identity = ApiManagementServiceIdentity(type="SystemAssigned")

    if enable_client_certificate is not None:
        instance.enable_client_certificate = enable_client_certificate

    if tags is not None:
        instance.tags = tags

    return instance


def list_apim(client, resource_group_name=None):
    """List all APIM instances.  Resource group is optional """
    if resource_group_name:
        return client.api_management_service.list_by_resource_group(resource_group_name)
    return client.api_management_service.list()


def get_apim(client, resource_group_name, name):
    """Show details of an APIM instance """
    return client.api_management_service.get(resource_group_name, name)


def check_name_availability(client, name):
    """checks to see if a service name is available to use """
    return client.api_management_service.check_name_availability(name)


def apim_backup(client, resource_group_name, name, backup_name, storage_account_name,
                storage_account_container, storage_account_key):
    """back up an API Management service to the configured storage account """
    parameters = ApiManagementServiceBackupRestoreParameters(
        storage_account=storage_account_name,
        access_key=storage_account_key,
        container_name=storage_account_container,
        backup_name=backup_name)

    return client.api_management_service.backup(resource_group_name, name, parameters)


def apim_apply_network_configuration_updates(client, resource_group_name, name, location=None):
    """back up an API Management service to the configured storage account """
    properties = {}
    if location is not None:
        properties['location'] = location

    return client.api_management_service.apply_network_configuration_updates(resource_group_name, name, properties)


# API Operations

def create_apim_api(client, resource_group_name, service_name, api_id, description=None, subscription_key_parameter_names=None,
                    api_revision=None, api_version=None, is_current=True, display_name=None, service_url=None, protocols=Protocol.https.value, path=None,
                    api_type=ApiType.http.value, subscription_required=False, tags=None, no_wait=False):
    """Creates a new API. """
    resource = ApiContract(
        api_id=api_id,
        description=description,
        subscription_key_parameter_names=subscription_key_parameter_names,
        api_revision=api_revision,
        api_version=api_version,
        is_current=is_current,
        display_name=display_name,
        service_url=service_url,
        protocols=protocols.split(','),
        path=path,
        api_type=api_type,
        subscription_required=subscription_required,
        tags=tags
    )

    cms = client.api

    return sdk_no_wait(no_wait, cms.create_or_update,
                       resource_group_name=resource_group_name,
                       service_name=service_name, api_id=api_id, parameters=resource)


def get_apim_api(client, resource_group_name, service_name, api_id):
    """Shows details of an API. """

    return client.api.get(resource_group_name, service_name, api_id)


def list_apim_api(client, resource_group_name, service_name):
    """List all APIs of an API Management instance. """

    return client.api.list_by_service(resource_group_name, service_name)


def delete_apim_api(client, resource_group_name, service_name, api_id, delete_revisions=True, no_wait=False):
    """Deletes an existing API. """

    cms = client.api

    return sdk_no_wait(no_wait, cms.delete, resource_group_name=resource_group_name, service_name=service_name, api_id=api_id, if_match='*', delete_revisions=delete_revisions)


def update_apim_api(instance, description=None, subscription_key_parameter_names=None,
                    api_revision=None, api_version=None, is_current=None, display_name=None, service_url=None, protocols=None, path=None,
                    api_type=None, subscription_required=None, tags=None):
    """Updates an existing API. """

    if description is not None:
        instance.description = description

    if subscription_key_parameter_names is not None:
        instance.subscription_key_parameter_names = subscription_key_parameter_names

    if api_revision is not None:
        instance.authentication_settings = api_revision

    if api_version is not None:
        instance.api_version = api_version

    if is_current is not None:
        instance.is_current = is_current

    if display_name is not None:
        instance.display_name = display_name

    if service_url is not None:
        instance.service_url = service_url

    if protocols is not None:
        instance.protocols = protocols.split(',')

    if path is not None:
        instance.path = path

    if api_type is not None:
        instance.api_type = api_type

    if subscription_required is not None:
        instance.subscription_required = subscription_required

    if tags is not None:
        instance.tags = tags

    return instance
