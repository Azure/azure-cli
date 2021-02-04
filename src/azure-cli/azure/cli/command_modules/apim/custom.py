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
                                             OpenIdAuthenticationSettingsContract, ProductContract, ProductState,
                                             NamedValueCreateContract, VersioningScheme, ApiVersionSetContract,
                                             OperationContract)

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
        resource.sku.capacity = 0

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


def apim_restore(client, resource_group_name, name, backup_name, storage_account_name,
                 storage_account_container, storage_account_key):
    """Restore an API Management service to the configured storage account """
    parameters = ApiManagementServiceBackupRestoreParameters(
        storage_account=storage_account_name,
        access_key=storage_account_key,
        container_name=storage_account_container,
        backup_name=backup_name)

    return client.api_management_service.restore(resource_group_name, name, parameters)


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

    return sdk_no_wait(no_wait, client.api.create_or_update,
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


# Product API Operations

def list_product_api(client, resource_group_name, service_name, product_id):

    return client.product_api.list_by_product(resource_group_name, service_name, product_id)


def check_product_exists(client, resource_group_name, service_name, product_id, api_id):

    return client.product_api.check_entity_exists(resource_group_name, service_name, product_id, api_id)


def add_product_api(client, resource_group_name, service_name, product_id, api_id, no_wait=False):

    return sdk_no_wait(
        no_wait,
        client.product_api.create_or_update,
        resource_group_name=resource_group_name,
        service_name=service_name,
        product_id=product_id,
        api_id=api_id)


def delete_product_api(client, resource_group_name, service_name, product_id, api_id, no_wait=False):

    return sdk_no_wait(
        no_wait,
        client.product_api.delete,
        resource_group_name=resource_group_name,
        service_name=service_name,
        product_id=product_id,
        api_id=api_id)


# Product Operations

def list_products(client, resource_group_name, service_name):

    return client.product.list_by_service(resource_group_name, service_name)


def show_product(client, resource_group_name, service_name, product_id):

    return client.product.get(resource_group_name, service_name, product_id)


def create_product(client, resource_group_name, service_name, product_name, product_id=None, description=None, legal_terms=None, subscription_required=None, approval_required=None, subscriptions_limit=None, state=None, no_wait=False):

    parameters = ProductContract(
        description=description,
        terms=legal_terms,
        subscription_required=subscription_required,
        display_name=product_name,
        approval_required=approval_required,
        subscriptions_limit=subscriptions_limit
    )

    # Possible values include: 'notPublished', 'published'
    if state is not None:
        if state == ProductState.not_published:
            parameters.state = ProductState.not_published
        elif state == ProductState.published:
            parameters.state = ProductState.published
        else:
            raise CLIError("State " + state + " is not supported.")

    if product_id is None:
        product_id = uuid.uuid4().hex

    return sdk_no_wait(
        no_wait,
        client.product.create_or_update,
        resource_group_name=resource_group_name,
        service_name=service_name,
        product_id=product_id,
        parameters=parameters)


def update_product(instance, product_name=None, description=None, legal_terms=None, subscription_required=None, approval_required=None, subscriptions_limit=None, state=None):

    if product_name is not None:
        instance.display_name = product_name

    if description is not None:
        instance.description = description

    if legal_terms is not None:
        instance.terms = legal_terms

    if subscription_required is not None:
        instance.subscription_required = subscription_required

    if approval_required is not None:
        instance.approval_required = approval_required

    if subscriptions_limit is not None:
        instance.subscriptions_limit = subscriptions_limit

    if state is not None:
        if state == ProductState.not_published:
            instance.state = ProductState.not_published
        elif state == ProductState.published:
            instance.state = ProductState.published
        else:
            raise CLIError("State " + state + " is not supported.")

    return instance


def delete_product(client, resource_group_name, service_name, product_id, delete_subscriptions=None, if_match=None, no_wait=False):

    return sdk_no_wait(
        no_wait,
        client.product.delete,
        resource_group_name=resource_group_name,
        service_name=service_name,
        product_id=product_id,
        delete_subscriptions=delete_subscriptions,
        if_match="*" if if_match is None else if_match)


# Named Value Operations

def create_apim_nv(client, resource_group_name, service_name, named_value_id, display_name, value=None, tags=None, secret=False):
    """Creates a new Named Value. """

    resource = NamedValueCreateContract(
        tags=tags,
        secret=secret,
        display_name=display_name,
        value=value
    )

    return client.named_value.create_or_update(resource_group_name, service_name, named_value_id, resource)


def get_apim_nv(client, resource_group_name, service_name, named_value_id):
    """Shows details of a Named Value. """

    return client.named_value.get(resource_group_name, service_name, named_value_id)


def get_apim_nv_secret(client, resource_group_name, service_name, named_value_id):
    """Gets the secret of the NamedValue."""

    return client.named_value.list_value(resource_group_name, service_name, named_value_id)


def list_apim_nv(client, resource_group_name, service_name):
    """List all Named Values of an API Management instance. """

    return client.named_value.list_by_service(resource_group_name, service_name)


def delete_apim_nv(client, resource_group_name, service_name, named_value_id):
    """Deletes an existing Named Value. """

    return client.named_value.delete(resource_group_name, service_name, named_value_id, if_match='*')


def update_apim_nv(instance, value=None, tags=None, secret=None):
    """Updates an existing Named Value."""
    if tags is not None:
        instance.tags = tags

    if value is not None:
        instance.value = value

    if secret is not None:
        instance.secret = secret

    return instance


def list_api_operation(client, resource_group_name, service_name, api_id):
    """List a collection of the operations for the specified API."""

    return client.api_operation.list_by_api(resource_group_name, service_name, api_id)


def get_api_operation(client, resource_group_name, service_name, api_id, operation_id):
    """Gets the details of the API Operation specified by its identifier."""

    return client.api_operation.get(resource_group_name, service_name, api_id, operation_id)


def create_api_operation(client, resource_group_name, service_name, api_id, url_template, method, display_name, template_parameters=None, operation_id=None, description=None, if_match=None, no_wait=False):
    """Creates a new operation in the API or updates an existing one."""

    if operation_id is None:
        operation_id = uuid.uuid4().hex

    resource = OperationContract(
        description=description,
        display_name=display_name,
        method=method,
        url_template=url_template,
        template_parameters=template_parameters)

    return sdk_no_wait(
        no_wait,
        client.api_operation.create_or_update,
        resource_group_name=resource_group_name,
        service_name=service_name,
        api_id=api_id,
        operation_id=operation_id,
        parameters=resource,
        if_match="*" if if_match is None else if_match)


def update_api_operation(instance, display_name=None, description=None, method=None, url_template=None):
    """Updates the details of the operation in the API specified by its identifier."""

    if display_name is not None:
        instance.display_name = display_name

    if description is not None:
        instance.description = description

    if method is not None:
        instance.method = method

    if url_template is not None:
        instance.url_template = url_template

    return instance


def delete_api_operation(client, resource_group_name, service_name, api_id, operation_id, if_match=None, no_wait=False):
    """Deletes the specified operation in the API."""

    return sdk_no_wait(
        no_wait,
        client.api_operation.delete,
        resource_group_name=resource_group_name,
        service_name=service_name,
        api_id=api_id,
        operation_id=operation_id,
        if_match="*" if if_match is None else if_match)


def list_api_release(client, resource_group_name, service_name, api_id):
    """Lists all releases of an API."""

    return client.api_release.list_by_service(resource_group_name, service_name, api_id)


def show_api_release(client, resource_group_name, service_name, api_id, release_id):
    """Returns the details of an API release."""

    return client.api_release.get(resource_group_name, service_name, api_id, release_id)


def create_api_release(client, resource_group_name, service_name, api_id, api_revision, release_id=None, if_match=None, notes=None):
    """Creates a new Release for the API."""

    if release_id is None:
        release_id = uuid.uuid4().hex

    api_id1 = "/apis/" + api_id + ";rev=" + api_revision

    return client.api_release.create_or_update(resource_group_name, service_name, api_id, release_id, "*" if if_match is None else if_match, api_id1, notes)


def update_api_release(instance, notes=None):
    """Updates the details of the release of the API specified by its identifier."""

    instance.notes = notes

    return instance


def delete_api_release(client, resource_group_name, service_name, api_id, release_id, if_match=None):
    """Deletes the specified release in the API."""

    return client.api_release.delete(resource_group_name, service_name, api_id, release_id, "*" if if_match is None else if_match)


def list_api_revision(client, resource_group_name, service_name, api_id):
    """Lists all revisions of an API."""

    return client.api_revision.list_by_service(resource_group_name, service_name, api_id)


def create_apim_api_revision(client, resource_group_name, service_name, api_id, api_revision, api_revision_description=None,
                             no_wait=False):
    """Creates a new API Revision. """

    cur_api = client.api.get(resource_group_name, service_name, api_id)

    resource = ApiCreateOrUpdateParameter(
        path=cur_api.path,
        display_name=cur_api.display_name,
        service_url=cur_api.service_url,
        authentication_settings=cur_api.authentication_settings,
        protocols=cur_api.protocols,
        subscription_key_parameter_names=cur_api.subscription_key_parameter_names,
        api_revision_description=api_revision_description,
        source_api_id="/apis/" + api_id
    )

    return sdk_no_wait(no_wait, client.api.create_or_update,
                       resource_group_name=resource_group_name, service_name=service_name,
                       api_id=api_id + ";rev=" + api_revision, parameters=resource)


def list_api_vs(client, resource_group_name, service_name):
    """Lists a collection of API Version Sets in the specified service instance."""

    return client.api_version_set.list_by_service(resource_group_name, service_name)


def show_api_vs(client, resource_group_name, service_name, version_set_id):
    """Gets the details of the Api Version Set specified by its identifier."""

    return client.api_version_set.get(resource_group_name, service_name, version_set_id)


def create_api_vs(client, resource_group_name, service_name, display_name, versioning_scheme, version_set_id=None, if_match=None, description=None, version_query_name=None, version_header_name=None, no_wait=False):
    """Creates or Updates a Api Version Set."""

    if version_set_id is None:
        version_set_id = uuid.uuid4().hex

    resource = ApiVersionSetContract(
        description=description,
        versioning_scheme=versioning_scheme,
        display_name=display_name)

    if versioning_scheme == VersioningScheme.header:
        if version_header_name is None:
            raise CLIError("Please specify version header name while using 'header' as version scheme.")

        resource.version_header_name = version_header_name

    if versioning_scheme == VersioningScheme.query:
        if version_query_name is None:
            raise CLIError("Please specify version query name while using 'query' as version scheme.")

        resource.version_query_name = version_query_name

    return sdk_no_wait(
        no_wait,
        client.api_version_set.create_or_update,
        resource_group_name=resource_group_name,
        service_name=service_name,
        version_set_id=version_set_id,
        parameters=resource,
        if_match="*" if if_match is None else if_match)


def update_api_apivs(instance, versioning_scheme=None, description=None, display_name=None, version_header_name=None, version_query_name=None):
    """Updates the details of the Api VersionSet specified by its identifier."""

    if display_name is not None:
        instance.display_name = display_name

    if versioning_scheme is not None:
        instance.versioning_scheme = versioning_scheme
        if versioning_scheme == VersioningScheme.header:
            if version_header_name is None:
                raise CLIError("Please specify version header name while using 'header' as version scheme.")

            instance.version_header_name = version_header_name
            instance.version_query_name = None
        if versioning_scheme == VersioningScheme.query:
            if version_query_name is None:
                raise CLIError("Please specify version query name while using 'query' as version scheme.")

            instance.version_query_name = version_query_name
            instance.version_header_name = None

    if description is None:
        instance.description = description

    return instance


def delete_api_vs(client, resource_group_name, service_name, version_set_id, if_match=None, no_wait=False):
    """Deletes specific Api Version Set."""

    return sdk_no_wait(
        no_wait,
        client.api_version_set.delete,
        resource_group_name=resource_group_name,
        service_name=service_name,
        version_set_id=version_set_id,
        if_match="*" if if_match is None else if_match)
