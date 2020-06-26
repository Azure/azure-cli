# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import uuid

from knack.util import CLIError
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.apimanagement.models import (ApiManagementServiceResource, ApiManagementServiceIdentity,
                                             ApiManagementServiceSkuProperties, ApiManagementServiceBackupRestoreParameters,
                                             VirtualNetworkType, SkuType, ApiType, ApiCreateOrUpdateParameter,
                                             ApiCreateOrUpdatePropertiesWsdlSelector, SoapApiType, ContentFormat)

# Service Operations


def create_apim(client, resource_group_name, name, publisher_email, sku_name=SkuType.developer.value,
                sku_capacity=1, virtual_network_type=VirtualNetworkType.none.value, enable_managed_identity=False,
                enable_client_certificate=None, publisher_name=None, location=None, tags=None, no_wait=False):

    resource = ApiManagementServiceResource(
        location=location,
        notification_sender_email=publisher_email,
        publisher_email=publisher_email,
        publisher_name=publisher_name,
        sku=ApiManagementServiceSkuProperties(
            name=sku_name, capacity=sku_capacity),
        enable_client_certificate=enable_client_certificate,
        virtual_network_type=VirtualNetworkType(virtual_network_type),
        tags=tags
    )

    if enable_managed_identity:
        resource['identity'] = ApiManagementServiceIdentity(
            type="SystemAssigned")

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
            instance.identity = ApiManagementServiceIdentity(
                type="SystemAssigned")

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


def import_apim_api(client, resource_group_name, service_name, api_path, description=None, subscription_key_parameter_names=None, api_revision=None,
                    api_id=None, api_version=None, api_version_set_id=None, display_name=None, service_url=None, protocols=None, specificationPath=None,
                    specificationUrl=None, specificationFormat=None, api_type=None, subscription_required=None,
                    soap_api_type=None, wsdl_endpoint_name=None, wsdl_service_name=None, no_wait=False):
    """Import a new API"""
    cms = client.api

    # should check api revision
    # should check apiId is not provided
    # possible format is 'wadl-xml', 'wadl-link-json', 'swagger-json', 'swagger-link-json', 'wsdl', 'wsdl-link', 'openapi', 'openapi+json', 'openapi-link'

    resource = ApiCreateOrUpdateParameter(
        format=specificationFormat,
        path=api_path
    )

    if api_revision is not None and api_id is not None:
        api_id = api_id+";rev="+api_revision
    elif api_id is None:
        api_id = uuid.uuid4().hex

    if specificationPath is not None:
        api_file = open(specificationPath, 'r')
        contentValue = api_file.read()
        resource.value = contentValue
    elif specificationUrl is not None:
        resource.value = specificationUrl
    else:
        raise CLIError("Can't specify specificationUrl and specificationPath")

    if protocols is not None:
        resource.protocols = protocols.split(',')

    if service_url is not None:
        resource.service_url = service_url

    if specificationFormat == ContentFormat.wsdl.value:
        if api_type == ApiType.http.value:
            soap_api_type = SoapApiType.soap_to_rest.value
        else:
            soap_api_type = SoapApiType.soap_pass_through.value

        resource.soap_api_type = soap_api_type

        if wsdl_service_name is not None and wsdl_endpoint_name is not None:
            resource.wsdl_selector = ApiCreateOrUpdatePropertiesWsdlSelector(
                wsdl_service_name=wsdl_service_name,
                wsdl_endpoint_name=wsdl_endpoint_name
            )

    if api_version is not None:
        resource.api_version = api_version

    if api_version_set_id is not None:
        resource.api_version_set_id = api_version_set_id

    if display_name is not None:
        resource.display_name = display_name

    if description is not None:
        resource.description = description

    if subscription_required is not None:
        resource.subscription_required = subscription_required

    if subscription_key_parameter_names is not None:
        resource.subscription_key_parameter_names = subscription_key_parameter_names

    return sdk_no_wait(no_wait, cms.create_or_update, resource_group_name=resource_group_name, service_name=service_name, api_id=api_id, parameters=resource)
