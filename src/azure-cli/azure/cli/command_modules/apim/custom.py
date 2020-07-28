# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, too-many-locals, too-many-arguments, too-many-statements, too-many-branches, no-else-return

import uuid
from knack.util import CLIError
from azure.cli.command_modules.apim._params import ImportFormat
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.apimanagement.models import (ApiManagementServiceResource, ApiManagementServiceIdentity,
                                             ApiManagementServiceSkuProperties, ApiManagementServiceBackupRestoreParameters,
                                             ApiContract, ApiType, ApiCreateOrUpdateParameter, Protocol,
                                             VirtualNetworkType, SkuType, ApiCreateOrUpdatePropertiesWsdlSelector,
                                             SoapApiType, ContentFormat, SubscriptionKeyParameterNamesContract,
                                             OAuth2AuthenticationSettingsContract, AuthenticationSettingsContract,
                                             OpenIdAuthenticationSettingsContract)

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

def create_apim_api(client, resource_group_name, service_name, api_id, description=None, subscription_key_header_name=None,
                    subscription_key_query_param_name=None, open_id_provider_id=None, bearer_token_sending_methods=None,
                    authorization_server_id=None, authorization_scope=None, display_name=None, service_url=None, protocols=None,
                    path=None, subscription_key_required=None, api_type=None,
                    subscription_required=False, no_wait=False):
    """Creates a new API. """

    if authorization_server_id is not None and authorization_scope is not None:
        o_auth2 = OAuth2AuthenticationSettingsContract(
            authorization_server_id=authorization_server_id,
            scope=authorization_scope
        )
        authentication_settings = AuthenticationSettingsContract(
            o_auth2=o_auth2,
            subscription_key_required=subscription_key_required
        )
    elif open_id_provider_id is not None and bearer_token_sending_methods is not None:
        openid = OpenIdAuthenticationSettingsContract(
            openid_provider_id=open_id_provider_id,
            bearer_token_sending_methods=bearer_token_sending_methods
        )
        authentication_settings = AuthenticationSettingsContract(
            openid=openid,
            subscription_key_required=subscription_key_required
        )
    else:
        authentication_settings = None

    resource = ApiContract(
        api_id=api_id,
        description=description,
        authentication_settings=authentication_settings,
        subscription_key_parameter_names=get_subscription_key_parameter_names(subscription_key_query_param_name, subscription_key_header_name),
        display_name=display_name,
        service_url=service_url,
        protocols=protocols if protocols is not None else [Protocol.https.value],
        path=path,
        api_type=api_type if api_type is not None else ApiType.http.value,
        subscription_required=subscription_required
    )

    cms = client.api

    return sdk_no_wait(no_wait, cms.create_or_update,
                       resource_group_name=resource_group_name,
                       service_name=service_name, api_id=api_id, parameters=resource)


def get_apim_api(client, resource_group_name, service_name, api_id):
    """Shows details of an API. """

    return client.api.get(resource_group_name, service_name, api_id)


def list_apim_api(client, resource_group_name, service_name, filter_display_name=None, top=None, skip=None):
    """List all APIs of an API Management instance. """

    if filter_display_name is not None:
        filter_display_name = "properties/displayName eq '%s'" % filter_display_name

    return client.api.list_by_service(resource_group_name, service_name, filter=filter_display_name, skip=skip, top=top)


def delete_apim_api(client, resource_group_name, service_name, api_id, delete_revisions=None, if_match=None, no_wait=False):
    """Deletes an existing API. """

    cms = client.api

    return sdk_no_wait(
        no_wait,
        cms.delete,
        resource_group_name=resource_group_name,
        service_name=service_name,
        api_id=api_id,
        if_match="*" if if_match is None else if_match,
        delete_revisions=delete_revisions if delete_revisions is not None else False)


def update_apim_api(instance, description=None, subscription_key_header_name=None, subscription_key_query_param_name=None,
                    display_name=None, service_url=None, protocols=None, path=None,
                    api_type=None, subscription_required=None, tags=None):
    """Updates an existing API. """

    if description is not None:
        instance.description = description

    if subscription_key_header_name is not None:
        instance.subscription_key_parameter_names = get_subscription_key_parameter_names(subscription_key_query_param_name, subscription_key_header_name)

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


def import_apim_api(client, resource_group_name, service_name, path, description=None, subscription_key_header_name=None,
                    subscription_key_query_param_name=None, api_id=None, api_revision=None, display_name=None, service_url=None,
                    protocols=None, specification_path=None, specification_url=None, specification_format=None,
                    api_type=None, subscription_required=None, soap_api_type=None, wsdl_endpoint_name=None,
                    wsdl_service_name=None, no_wait=False):
    """Import a new API"""
    cms = client.api

    # api_type: Type of API. Possible values include: 'http', 'soap'
    # possible parameter format is 'wadl-xml', 'wadl-link-json', 'swagger-json', 'swagger-link-json', 'wsdl', 'wsdl-link', 'openapi', 'openapi+json', 'openapi-link'
    # possible parameter specificationFormat is 'Wadl', 'Swagger', 'OpenApi', 'OpenApiJson', 'Wsdl'

    if specification_format == ImportFormat.Wadl.value:
        s_format = ContentFormat.wadl_xml.value if specification_path is not None else ContentFormat.wadl_link_json.value
    elif specification_format == ImportFormat.Swagger.value:
        s_format = ContentFormat.swagger_json.value if specification_path is not None else ContentFormat.swagger_link_json.value
    elif specification_format == ImportFormat.OpenApi.value:
        s_format = ContentFormat.openapi.value if specification_path is not None else ContentFormat.openapi_link.value
    elif specification_format == ImportFormat.OpenApiJson.value:
        s_format = ContentFormat.openapijson.value if specification_path is not None else ContentFormat.openapi_link.value
    elif specification_format == ImportFormat.Wsdl.value:
        s_format = ContentFormat.wsdl.value if specification_path is not None else ContentFormat.wsdl_link.value
    else:
        raise CLIError("Please provide valid value for specificationFormat: " + specification_format)

    resource = ApiCreateOrUpdateParameter(
        format=s_format,
        path=path
    )

    if api_revision is not None and api_id is not None:
        api_id = api_id + ";rev=" + api_revision
    elif api_id is None:
        api_id = uuid.uuid4().hex

    if specification_path is not None and specification_url is None:
        api_file = open(specification_path, 'r')
        content_value = api_file.read()
        resource.value = content_value
    elif specification_url is not None and specification_path is None:
        resource.value = specification_url
    elif specification_path is not None and specification_url is not None:
        raise CLIError("Can't specify specification-url and specification-path at the same time.")
    else:
        raise CLIError("Please either specify specification-url or specification-path.")

    resource.protocols = protocols
    resource.service_url = service_url
    resource.display_name = display_name
    resource.description = description
    resource.subscription_required = subscription_required
    resource.subscription_key_parameter_names = get_subscription_key_parameter_names(subscription_key_query_param_name, subscription_key_header_name)

    if specification_format == ImportFormat.Wsdl.value:
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

    return sdk_no_wait(no_wait, cms.create_or_update, resource_group_name=resource_group_name, service_name=service_name, api_id=api_id, parameters=resource)


def get_subscription_key_parameter_names(subscription_key_header_name=None, subscription_key_query_param_name=None):
    if subscription_key_query_param_name is not None and subscription_key_header_name is not None:
        return SubscriptionKeyParameterNamesContract(
            header=subscription_key_header_name,
            query=subscription_key_query_param_name
        )
    elif subscription_key_query_param_name is not None or subscription_key_header_name is not None:
        raise CLIError("Please specify 'subscription_key_query_param_name' and 'subscription_key_header_name' at the same time.")

    return None
