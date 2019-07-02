# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import (
    tags_type,
    get_resource_name_completion_list,
    quotes,
    get_three_state_flag,
    get_enum_type
)
from azure.cli.core.commands.validators import get_default_location_from_resource_group


def load_arguments(self, _):
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt api create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('description', id_part=None, help='Description of the API. May include HTML formatting tags.') # str
        c.argument('authentication_settings', id_part=None, help='Collection of authentication settings included into this API.') # dict
        c.argument('subscription_key_parameter_names', id_part=None, help='Protocols over which API is made available.') # dict
        c.argument('type', id_part=None, help='Type of API.') # str
        c.argument('api_revision', id_part=None, help='Describes the Revision of the Api. If no value is provided, default revision 1 is created') # str
        c.argument('api_version', id_part=None, help='Indicates the Version identifier of the API if the API is versioned') # str
        c.argument('is_current', arg_type=get_three_state_flag(), id_part=None, help='Indicates if API revision is current api revision.') # boolean
        c.argument('api_revision_description', id_part=None, help='Description of the Api Revision.') # str
        c.argument('api_version_description', id_part=None, help='Description of the Api Version.') # str
        c.argument('api_version_set_id', id_part=None, help='A resource identifier for the related ApiVersionSet.') # str
        c.argument('subscription_required', arg_type=get_three_state_flag(), id_part=None, help='Specifies whether an API or Product subscription is required for accessing the API.') # boolean
        c.argument('source_api_id', id_part=None, help='API identifier of the source API.') # str
        c.argument('display_name', id_part=None, help='API name. Must be 1 to 300 characters long.') # str
        c.argument('service_url', id_part=None, help='Absolute URL of the backend service implementing this API. Cannot be more than 2000 characters long.') # str
        c.argument('path', id_part=None, help='Relative URL uniquely identifying this API and all of its resource paths within the API Management service instance. It is appended to the API endpoint base URL specified during the service instance creation to form a public URL for this API.') # str
        c.argument('protocols', id_part=None, help='Describes on which protocols the operations in this API can be invoked.') # list
        c.argument('api_version_set', id_part=None, help='Version set details') # dict
        c.argument('value', id_part=None, help='Content value when Importing an API.') # str
        c.argument('format', id_part=None, help='Format of the Content in which the API is getting imported.') # str
        c.argument('wsdl_selector', id_part=None, help='Criteria to limit import of WSDL to a subset of the document.') # dict
        c.argument('api_type', id_part=None, help='Type of Api to create. <br> * `http` creates a SOAP to REST API <br> * `soap` creates a SOAP pass-through API .') # str

    with self.argument_context('apimgmt api update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('description', id_part=None, help='Description of the API. May include HTML formatting tags.') # str
        c.argument('authentication_settings', id_part=None, help='Collection of authentication settings included into this API.') # dict
        c.argument('subscription_key_parameter_names', id_part=None, help='Protocols over which API is made available.') # dict
        c.argument('type', id_part=None, help='Type of API.') # str
        c.argument('api_revision', id_part=None, help='Describes the Revision of the Api. If no value is provided, default revision 1 is created') # str
        c.argument('api_version', id_part=None, help='Indicates the Version identifier of the API if the API is versioned') # str
        c.argument('is_current', arg_type=get_three_state_flag(), id_part=None, help='Indicates if API revision is current api revision.') # boolean
        c.argument('api_revision_description', id_part=None, help='Description of the Api Revision.') # str
        c.argument('api_version_description', id_part=None, help='Description of the Api Version.') # str
        c.argument('api_version_set_id', id_part=None, help='A resource identifier for the related ApiVersionSet.') # str
        c.argument('subscription_required', arg_type=get_three_state_flag(), id_part=None, help='Specifies whether an API or Product subscription is required for accessing the API.') # boolean
        c.argument('source_api_id', id_part=None, help='API identifier of the source API.') # str
        c.argument('display_name', id_part=None, help='API name. Must be 1 to 300 characters long.') # str
        c.argument('service_url', id_part=None, help='Absolute URL of the backend service implementing this API. Cannot be more than 2000 characters long.') # str
        c.argument('path', id_part=None, help='Relative URL uniquely identifying this API and all of its resource paths within the API Management service instance. It is appended to the API endpoint base URL specified during the service instance creation to form a public URL for this API.') # str
        c.argument('protocols', id_part=None, help='Describes on which protocols the operations in this API can be invoked.') # list
        c.argument('api_version_set', id_part=None, help='Version set details') # dict
        c.argument('value', id_part=None, help='Content value when Importing an API.') # str
        c.argument('format', id_part=None, help='Format of the Content in which the API is getting imported.') # str
        c.argument('wsdl_selector', id_part=None, help='Criteria to limit import of WSDL to a subset of the document.') # dict
        c.argument('api_type', id_part=None, help='Type of Api to create. <br> * `http` creates a SOAP to REST API <br> * `soap` creates a SOAP pass-through API .') # str

    with self.argument_context('apimgmt api delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str

    with self.argument_context('apimgmt api list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt api show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt api release create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('release_id', id_part=None, help='Release identifier within an API. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('notes', id_part=None, help='Release Notes') # str

    with self.argument_context('apimgmt api release update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('release_id', id_part=None, help='Release identifier within an API. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('notes', id_part=None, help='Release Notes') # str

    with self.argument_context('apimgmt api release delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('release_id', id_part=None, help='Release identifier within an API. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt api release list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt api release show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('release_id', id_part=None, help='Release identifier within an API. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt api operation create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('operation_id', id_part=None, help='Operation identifier within an API. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('template_parameters', id_part=None, help='Collection of URL template parameters.') # list
        c.argument('description', id_part=None, help='Description of the operation. May include HTML formatting tags.') # str
        c.argument('request', id_part=None, help='An entity containing request details.') # dict
        c.argument('responses', id_part=None, help='Array of Operation responses.') # list
        c.argument('policies', id_part=None, help='Operation Policies') # str
        c.argument('display_name', id_part=None, help='Operation Name.') # str
        c.argument('method', id_part=None, help='A Valid HTTP Operation Method. Typical Http Methods like GET, PUT, POST but not limited by only them.') # str
        c.argument('url_template', id_part=None, help='Relative URL template identifying the target resource for this operation. May include parameters. Example: /customers/{cid}/orders/{oid}/?date={date}') # str

    with self.argument_context('apimgmt api operation update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('operation_id', id_part=None, help='Operation identifier within an API. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('template_parameters', id_part=None, help='Collection of URL template parameters.') # list
        c.argument('description', id_part=None, help='Description of the operation. May include HTML formatting tags.') # str
        c.argument('request', id_part=None, help='An entity containing request details.') # dict
        c.argument('responses', id_part=None, help='Array of Operation responses.') # list
        c.argument('policies', id_part=None, help='Operation Policies') # str
        c.argument('display_name', id_part=None, help='Operation Name.') # str
        c.argument('method', id_part=None, help='A Valid HTTP Operation Method. Typical Http Methods like GET, PUT, POST but not limited by only them.') # str
        c.argument('url_template', id_part=None, help='Relative URL template identifying the target resource for this operation. May include parameters. Example: /customers/{cid}/orders/{oid}/?date={date}') # str

    with self.argument_context('apimgmt api operation delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('operation_id', id_part=None, help='Operation identifier within an API. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt api operation list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str

    with self.argument_context('apimgmt api operation show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('operation_id', id_part=None, help='Operation identifier within an API. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt api operation policy create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('operation_id', id_part=None, help='Operation identifier within an API. Must be unique in the current API Management service instance.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('value', id_part=None, help='Contents of the Policy as defined by the format.') # str
        c.argument('format', id_part=None, help='Format of the policyContent.') # str

    with self.argument_context('apimgmt api operation policy update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('operation_id', id_part=None, help='Operation identifier within an API. Must be unique in the current API Management service instance.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('value', id_part=None, help='Contents of the Policy as defined by the format.') # str
        c.argument('format', id_part=None, help='Format of the policyContent.') # str

    with self.argument_context('apimgmt api operation policy delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('operation_id', id_part=None, help='Operation identifier within an API. Must be unique in the current API Management service instance.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str

    with self.argument_context('apimgmt api operation policy list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('operation_id', id_part=None, help='Operation identifier within an API. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt api operation policy show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('operation_id', id_part=None, help='Operation identifier within an API. Must be unique in the current API Management service instance.') # str
        c.argument('format', id_part=None, help='Format of the policyContent.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt tag create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('tag_id', id_part=None, help='Tag identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('display_name', id_part=None, help='Tag name.') # str

    with self.argument_context('apimgmt tag update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('tag_id', id_part=None, help='Tag identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('display_name', id_part=None, help='Tag name.') # str

    with self.argument_context('apimgmt tag delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('tag_id', id_part=None, help='Tag identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt tag list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt tag show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('tag_id', id_part=None, help='Tag identifier. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt api policy create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('value', id_part=None, help='Contents of the Policy as defined by the format.') # str
        c.argument('format', id_part=None, help='Format of the policyContent.') # str

    with self.argument_context('apimgmt api policy update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('value', id_part=None, help='Contents of the Policy as defined by the format.') # str
        c.argument('format', id_part=None, help='Format of the policyContent.') # str

    with self.argument_context('apimgmt api policy delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str

    with self.argument_context('apimgmt api policy list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str

    with self.argument_context('apimgmt api policy show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str
        c.argument('format', id_part=None, help='Format of the policyContent.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt api schema create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('schema_id', id_part=None, help='Schema identifier within an API. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('content_type', id_part=None, help='Must be a valid a media type used in a Content-Type header as defined in the RFC 2616. Media type of the schema document (e.g. application/json, application/xml). </br> - `Swagger` Schema use `application/vnd.ms-azure-apim.swagger.definitions+json` </br> - `WSDL` Schema use `application/vnd.ms-azure-apim.xsd+xml` </br> - `OpenApi` Schema use `application/vnd.oai.openapi.components+json` </br> - `WADL Schema` use `application/vnd.ms-azure-apim.wadl.grammars+xml`.') # str
        c.argument('document', id_part=None, help='Create or update Properties of the Schema Document.') # dict

    with self.argument_context('apimgmt api schema update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('schema_id', id_part=None, help='Schema identifier within an API. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('content_type', id_part=None, help='Must be a valid a media type used in a Content-Type header as defined in the RFC 2616. Media type of the schema document (e.g. application/json, application/xml). </br> - `Swagger` Schema use `application/vnd.ms-azure-apim.swagger.definitions+json` </br> - `WSDL` Schema use `application/vnd.ms-azure-apim.xsd+xml` </br> - `OpenApi` Schema use `application/vnd.oai.openapi.components+json` </br> - `WADL Schema` use `application/vnd.ms-azure-apim.wadl.grammars+xml`.') # str
        c.argument('document', id_part=None, help='Create or update Properties of the Schema Document.') # dict

    with self.argument_context('apimgmt api schema delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('schema_id', id_part=None, help='Schema identifier within an API. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt api schema list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str

    with self.argument_context('apimgmt api schema show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('schema_id', id_part=None, help='Schema identifier within an API. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt api diagnostic create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('diagnostic_id', id_part=None, help='Diagnostic identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('always_log', id_part=None, help='Specifies for what type of messages sampling settings should not apply.') # str
        c.argument('logger_id', id_part=None, help='Resource Id of a target logger.') # str
        c.argument('sampling', id_part=None, help='Sampling settings for Diagnostic.') # dict
        c.argument('frontend', id_part=None, help='Diagnostic settings for incoming/outgoing HTTP messages to the Gateway.') # dict
        c.argument('backend', id_part=None, help='Diagnostic settings for incoming/outgoing HTTP messages to the Backend') # dict
        c.argument('enable_http_correlation_headers', arg_type=get_three_state_flag(), id_part=None, help='Whether to process Correlation Headers coming to Api Management Service. Only applicable to Application Insights diagnostics. Default is true.') # boolean

    with self.argument_context('apimgmt api diagnostic update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('diagnostic_id', id_part=None, help='Diagnostic identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('always_log', id_part=None, help='Specifies for what type of messages sampling settings should not apply.') # str
        c.argument('logger_id', id_part=None, help='Resource Id of a target logger.') # str
        c.argument('sampling', id_part=None, help='Sampling settings for Diagnostic.') # dict
        c.argument('frontend', id_part=None, help='Diagnostic settings for incoming/outgoing HTTP messages to the Gateway.') # dict
        c.argument('backend', id_part=None, help='Diagnostic settings for incoming/outgoing HTTP messages to the Backend') # dict
        c.argument('enable_http_correlation_headers', arg_type=get_three_state_flag(), id_part=None, help='Whether to process Correlation Headers coming to Api Management Service. Only applicable to Application Insights diagnostics. Default is true.') # boolean

    with self.argument_context('apimgmt api diagnostic delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('diagnostic_id', id_part=None, help='Diagnostic identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt api diagnostic list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt api diagnostic show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('diagnostic_id', id_part=None, help='Diagnostic identifier. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt api issue create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('issue_id', id_part=None, help='Issue identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('created_date', id_part=None, help='Date and time when the issue was created.') # datetime
        c.argument('state', id_part=None, help='Status of the issue.') # str
        c.argument('title', id_part=None, help='The issue title.') # str
        c.argument('description', id_part=None, help='Text describing the issue.') # str
        c.argument('user_id', id_part=None, help='A resource identifier for the user created the issue.') # str

    with self.argument_context('apimgmt api issue update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('issue_id', id_part=None, help='Issue identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('created_date', id_part=None, help='Date and time when the issue was created.') # datetime
        c.argument('state', id_part=None, help='Status of the issue.') # str
        c.argument('title', id_part=None, help='The issue title.') # str
        c.argument('description', id_part=None, help='Text describing the issue.') # str
        c.argument('user_id', id_part=None, help='A resource identifier for the user created the issue.') # str

    with self.argument_context('apimgmt api issue delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('issue_id', id_part=None, help='Issue identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt api issue list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt api issue show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('issue_id', id_part=None, help='Issue identifier. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt api issue comment create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('issue_id', id_part=None, help='Issue identifier. Must be unique in the current API Management service instance.') # str
        c.argument('comment_id', id_part=None, help='Comment identifier within an Issue. Must be unique in the current Issue.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('text', id_part=None, help='Comment text.') # str
        c.argument('created_date', id_part=None, help='Date and time when the comment was created.') # datetime
        c.argument('user_id', id_part=None, help='A resource identifier for the user who left the comment.') # str

    with self.argument_context('apimgmt api issue comment update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('issue_id', id_part=None, help='Issue identifier. Must be unique in the current API Management service instance.') # str
        c.argument('comment_id', id_part=None, help='Comment identifier within an Issue. Must be unique in the current Issue.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('text', id_part=None, help='Comment text.') # str
        c.argument('created_date', id_part=None, help='Date and time when the comment was created.') # datetime
        c.argument('user_id', id_part=None, help='A resource identifier for the user who left the comment.') # str

    with self.argument_context('apimgmt api issue comment delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('issue_id', id_part=None, help='Issue identifier. Must be unique in the current API Management service instance.') # str
        c.argument('comment_id', id_part=None, help='Comment identifier within an Issue. Must be unique in the current Issue.') # str

    with self.argument_context('apimgmt api issue comment list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('issue_id', id_part=None, help='Issue identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt api issue comment show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('issue_id', id_part=None, help='Issue identifier. Must be unique in the current API Management service instance.') # str
        c.argument('comment_id', id_part=None, help='Comment identifier within an Issue. Must be unique in the current Issue.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt api issue attachment create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('issue_id', id_part=None, help='Issue identifier. Must be unique in the current API Management service instance.') # str
        c.argument('attachment_id', id_part=None, help='Attachment identifier within an Issue. Must be unique in the current Issue.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('title', id_part=None, help='Filename by which the binary data will be saved.') # str
        c.argument('content_format', id_part=None, help='Either \'link\' if content is provided via an HTTP link or the MIME type of the Base64-encoded binary data provided in the \'content\' property.') # str
        c.argument('content', id_part=None, help='An HTTP link or Base64-encoded binary data.') # str

    with self.argument_context('apimgmt api issue attachment update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('issue_id', id_part=None, help='Issue identifier. Must be unique in the current API Management service instance.') # str
        c.argument('attachment_id', id_part=None, help='Attachment identifier within an Issue. Must be unique in the current Issue.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('title', id_part=None, help='Filename by which the binary data will be saved.') # str
        c.argument('content_format', id_part=None, help='Either \'link\' if content is provided via an HTTP link or the MIME type of the Base64-encoded binary data provided in the \'content\' property.') # str
        c.argument('content', id_part=None, help='An HTTP link or Base64-encoded binary data.') # str

    with self.argument_context('apimgmt api issue attachment delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('issue_id', id_part=None, help='Issue identifier. Must be unique in the current API Management service instance.') # str
        c.argument('attachment_id', id_part=None, help='Attachment identifier within an Issue. Must be unique in the current Issue.') # str

    with self.argument_context('apimgmt api issue attachment list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('issue_id', id_part=None, help='Issue identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt api issue attachment show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API identifier. Must be unique in the current API Management service instance.') # str
        c.argument('issue_id', id_part=None, help='Issue identifier. Must be unique in the current API Management service instance.') # str
        c.argument('attachment_id', id_part=None, help='Attachment identifier within an Issue. Must be unique in the current Issue.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt api tagdescription create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('tag_id', id_part=None, help='Tag identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('description', id_part=None, help='Description of the Tag.') # str
        c.argument('external_docs_url', id_part=None, help='Absolute URL of external resources describing the tag.') # str
        c.argument('external_docs_description', id_part=None, help='Description of the external resources describing the tag.') # str

    with self.argument_context('apimgmt api tagdescription update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('tag_id', id_part=None, help='Tag identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('description', id_part=None, help='Description of the Tag.') # str
        c.argument('external_docs_url', id_part=None, help='Absolute URL of external resources describing the tag.') # str
        c.argument('external_docs_description', id_part=None, help='Description of the external resources describing the tag.') # str

    with self.argument_context('apimgmt api tagdescription delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('tag_id', id_part=None, help='Tag identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt api tagdescription list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str

    with self.argument_context('apimgmt api tagdescription show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('tag_id', id_part=None, help='Tag identifier. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt apiversionset create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('version_set_id', id_part=None, help='Api Version Set identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('description', id_part=None, help='Description of API Version Set.') # str
        c.argument('version_query_name', id_part=None, help='Name of query parameter that indicates the API Version if versioningScheme is set to `query`.') # str
        c.argument('version_header_name', id_part=None, help='Name of HTTP header parameter that indicates the API Version if versioningScheme is set to `header`.') # str
        c.argument('display_name', id_part=None, help='Name of API Version Set') # str
        c.argument('versioning_scheme', id_part=None, help='An value that determines where the API Version identifer will be located in a HTTP request.') # str

    with self.argument_context('apimgmt apiversionset update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('version_set_id', id_part=None, help='Api Version Set identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('description', id_part=None, help='Description of API Version Set.') # str
        c.argument('version_query_name', id_part=None, help='Name of query parameter that indicates the API Version if versioningScheme is set to `query`.') # str
        c.argument('version_header_name', id_part=None, help='Name of HTTP header parameter that indicates the API Version if versioningScheme is set to `header`.') # str
        c.argument('display_name', id_part=None, help='Name of API Version Set') # str
        c.argument('versioning_scheme', id_part=None, help='An value that determines where the API Version identifer will be located in a HTTP request.') # str

    with self.argument_context('apimgmt apiversionset delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('version_set_id', id_part=None, help='Api Version Set identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt apiversionset list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt apiversionset show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('version_set_id', id_part=None, help='Api Version Set identifier. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt authorizationserver create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('authsid', id_part=None, help='Identifier of the authorization server.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('description', id_part=None, help='Description of the authorization server. Can contain HTML formatting tags.') # str
        c.argument('authorization_methods', id_part=None, help='HTTP verbs supported by the authorization endpoint. GET must be always present. POST is optional.') # list
        c.argument('client_authentication_method', id_part=None, help='Method of authentication supported by the token endpoint of this authorization server. Possible values are Basic and/or Body. When Body is specified, client credentials and other parameters are passed within the request body in the application/x-www-form-urlencoded format.') # list
        c.argument('token_body_parameters', id_part=None, help='Additional parameters required by the token endpoint of this authorization server represented as an array of JSON objects with name and value string properties, i.e. {"name" : "name value", "value": "a value"}.') # list
        c.argument('token_endpoint', id_part=None, help='OAuth token endpoint. Contains absolute URI to entity being referenced.') # str
        c.argument('support_state', arg_type=get_three_state_flag(), id_part=None, help='If true, authorization server will include state parameter from the authorization request to its response. Client may use state parameter to raise protocol security.') # boolean
        c.argument('default_scope', id_part=None, help='Access token scope that is going to be requested by default. Can be overridden at the API level. Should be provided in the form of a string containing space-delimited values.') # str
        c.argument('bearer_token_sending_methods', id_part=None, help='Specifies the mechanism by which access token is passed to the API. ') # list
        c.argument('client_secret', id_part=None, help='Client or app secret registered with this authorization server.') # str
        c.argument('resource_owner_username', id_part=None, help='Can be optionally specified when resource owner password grant type is supported by this authorization server. Default resource owner username.') # str
        c.argument('resource_owner_password', id_part=None, help='Can be optionally specified when resource owner password grant type is supported by this authorization server. Default resource owner password.') # str
        c.argument('display_name', id_part=None, help='User-friendly authorization server name.') # str
        c.argument('client_registration_endpoint', id_part=None, help='Optional reference to a page where client or app registration for this authorization server is performed. Contains absolute URL to entity being referenced.') # str
        c.argument('authorization_endpoint', id_part=None, help='OAuth authorization endpoint. See http://tools.ietf.org/html/rfc6749#section-3.2.') # str
        c.argument('grant_types', id_part=None, help='Form of an authorization grant, which the client uses to request the access token.') # list
        c.argument('client_id', id_part=None, help='Client or app id registered with this authorization server.') # str

    with self.argument_context('apimgmt authorizationserver update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('authsid', id_part=None, help='Identifier of the authorization server.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('description', id_part=None, help='Description of the authorization server. Can contain HTML formatting tags.') # str
        c.argument('authorization_methods', id_part=None, help='HTTP verbs supported by the authorization endpoint. GET must be always present. POST is optional.') # list
        c.argument('client_authentication_method', id_part=None, help='Method of authentication supported by the token endpoint of this authorization server. Possible values are Basic and/or Body. When Body is specified, client credentials and other parameters are passed within the request body in the application/x-www-form-urlencoded format.') # list
        c.argument('token_body_parameters', id_part=None, help='Additional parameters required by the token endpoint of this authorization server represented as an array of JSON objects with name and value string properties, i.e. {"name" : "name value", "value": "a value"}.') # list
        c.argument('token_endpoint', id_part=None, help='OAuth token endpoint. Contains absolute URI to entity being referenced.') # str
        c.argument('support_state', arg_type=get_three_state_flag(), id_part=None, help='If true, authorization server will include state parameter from the authorization request to its response. Client may use state parameter to raise protocol security.') # boolean
        c.argument('default_scope', id_part=None, help='Access token scope that is going to be requested by default. Can be overridden at the API level. Should be provided in the form of a string containing space-delimited values.') # str
        c.argument('bearer_token_sending_methods', id_part=None, help='Specifies the mechanism by which access token is passed to the API. ') # list
        c.argument('client_secret', id_part=None, help='Client or app secret registered with this authorization server.') # str
        c.argument('resource_owner_username', id_part=None, help='Can be optionally specified when resource owner password grant type is supported by this authorization server. Default resource owner username.') # str
        c.argument('resource_owner_password', id_part=None, help='Can be optionally specified when resource owner password grant type is supported by this authorization server. Default resource owner password.') # str
        c.argument('display_name', id_part=None, help='User-friendly authorization server name.') # str
        c.argument('client_registration_endpoint', id_part=None, help='Optional reference to a page where client or app registration for this authorization server is performed. Contains absolute URL to entity being referenced.') # str
        c.argument('authorization_endpoint', id_part=None, help='OAuth authorization endpoint. See http://tools.ietf.org/html/rfc6749#section-3.2.') # str
        c.argument('grant_types', id_part=None, help='Form of an authorization grant, which the client uses to request the access token.') # list
        c.argument('client_id', id_part=None, help='Client or app id registered with this authorization server.') # str

    with self.argument_context('apimgmt authorizationserver delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('authsid', id_part=None, help='Identifier of the authorization server.') # str

    with self.argument_context('apimgmt authorizationserver list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt authorizationserver show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('authsid', id_part=None, help='Identifier of the authorization server.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt backend create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('backend_id', id_part=None, help='Identifier of the Backend entity. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('title', id_part=None, help='Backend Title.') # str
        c.argument('description', id_part=None, help='Backend Description.') # str
        c.argument('resource_id', id_part=None, help='Management Uri of the Resource in External System. This url can be the Arm Resource Id of Logic Apps, Function Apps or Api Apps.') # str
        c.argument('service_fabric_cluster', id_part=None, help='Backend Service Fabric Cluster Properties') # dict
        c.argument('credentials', id_part=None, help='Backend Credentials Contract Properties') # dict
        c.argument('proxy', id_part=None, help='Backend Proxy Contract Properties') # dict
        c.argument('tls', id_part=None, help='Backend TLS Properties') # dict
        c.argument('url', id_part=None, help='Runtime Url of the Backend.') # str
        c.argument('protocol', id_part=None, help='Backend communication protocol.') # str

    with self.argument_context('apimgmt backend update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('backend_id', id_part=None, help='Identifier of the Backend entity. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('title', id_part=None, help='Backend Title.') # str
        c.argument('description', id_part=None, help='Backend Description.') # str
        c.argument('resource_id', id_part=None, help='Management Uri of the Resource in External System. This url can be the Arm Resource Id of Logic Apps, Function Apps or Api Apps.') # str
        c.argument('service_fabric_cluster', id_part=None, help='Backend Service Fabric Cluster Properties') # dict
        c.argument('credentials', id_part=None, help='Backend Credentials Contract Properties') # dict
        c.argument('proxy', id_part=None, help='Backend Proxy Contract Properties') # dict
        c.argument('tls', id_part=None, help='Backend TLS Properties') # dict
        c.argument('url', id_part=None, help='Runtime Url of the Backend.') # str
        c.argument('protocol', id_part=None, help='Backend communication protocol.') # str

    with self.argument_context('apimgmt backend delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('backend_id', id_part=None, help='Identifier of the Backend entity. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt backend list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt backend show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('backend_id', id_part=None, help='Identifier of the Backend entity. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt cache create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('cache_id', id_part=None, help='Identifier of the Cache entity. Cache identifier (should be either \'default\' or valid Azure region identifier).') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('description', id_part=None, help='Cache description') # str
        c.argument('connection_string', id_part=None, help='Runtime connection string to cache') # str
        c.argument('resource_id', id_part=None, help='Original uri of entity in external system cache points to') # str

    with self.argument_context('apimgmt cache update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('cache_id', id_part=None, help='Identifier of the Cache entity. Cache identifier (should be either \'default\' or valid Azure region identifier).') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('description', id_part=None, help='Cache description') # str
        c.argument('connection_string', id_part=None, help='Runtime connection string to cache') # str
        c.argument('resource_id', id_part=None, help='Original uri of entity in external system cache points to') # str

    with self.argument_context('apimgmt cache delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('cache_id', id_part=None, help='Identifier of the Cache entity. Cache identifier (should be either \'default\' or valid Azure region identifier).') # str

    with self.argument_context('apimgmt cache list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt cache show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('cache_id', id_part=None, help='Identifier of the Cache entity. Cache identifier (should be either \'default\' or valid Azure region identifier).') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt certificate create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('certificate_id', id_part=None, help='Identifier of the certificate entity. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('data', id_part=None, help='Base 64 encoded certificate using the application/x-pkcs12 representation.') # str
        c.argument('password', id_part=None, help='Password for the Certificate') # str

    with self.argument_context('apimgmt certificate update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('certificate_id', id_part=None, help='Identifier of the certificate entity. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('data', id_part=None, help='Base 64 encoded certificate using the application/x-pkcs12 representation.') # str
        c.argument('password', id_part=None, help='Password for the Certificate') # str

    with self.argument_context('apimgmt certificate delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('certificate_id', id_part=None, help='Identifier of the certificate entity. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt certificate list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt certificate show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('certificate_id', id_part=None, help='Identifier of the certificate entity. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('name', id_part=None, help='The name of the API Management service.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('tags', id_part=None, help='Resource tags.') # dictionary
        c.argument('notification_sender_email', id_part=None, help='Email address from which the notification will be sent.') # str
        c.argument('hostname_configurations', id_part=None, help='Custom hostname configuration of the API Management service.') # list
        c.argument('virtual_network_configuration', id_part=None, help='Virtual network configuration of the API Management service.') # dict
        c.argument('additional_locations', id_part=None, help='Additional datacenter locations of the API Management service.') # list
        c.argument('custom_properties', id_part=None, help='Custom properties of the API Management service.</br>Setting `Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Ciphers.TripleDes168` will disable the cipher TLS_RSA_WITH_3DES_EDE_CBC_SHA for all TLS(1.0, 1.1 and 1.2).</br>Setting `Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls11` can be used to disable just TLS 1.1.</br>Setting `Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls10` can be used to disable TLS 1.0 on an API Management service.</br>Setting `Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls11` can be used to disable just TLS 1.1 for communications with backends.</br>Setting `Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls10` can be used to disable TLS 1.0 for communications with backends.</br>Setting `Microsoft.WindowsAzure.ApiManagement.Gateway.Protocols.Server.Http2` can be used to enable HTTP2 protocol on an API Management service.</br>Not specifying any of these properties on PATCH operation will reset omitted properties\' values to their defaults. For all the settings except Http2 the default value is `True` if the service was created on or before April 1st 2018 and `False` otherwise. Http2 setting\'s default value is `False`.') # dictionary
        c.argument('certificates', id_part=None, help='List of Certificates that need to be installed in the API Management service. Max supported certificates that can be installed is 10.') # list
        c.argument('enable_client_certificate', arg_type=get_three_state_flag(), id_part=None, help='Property only meant to be used for Consumption SKU Service. This enforces a client certificate to be presented on each request to the gateway. This also enables the ability to authenticate the certificate in the policy on the gateway.') # boolean
        c.argument('virtual_network_type', id_part=None, help='The type of VPN in which API Management service needs to be configured in. None (Default Value) means the API Management service is not part of any Virtual Network, External means the API Management deployment is set up inside a Virtual Network having an Internet Facing Endpoint, and Internal means that API Management deployment is setup inside a Virtual Network having an Intranet Facing Endpoint only.') # str
        c.argument('publisher_email', id_part=None, help='Publisher email.') # str
        c.argument('publisher_name', id_part=None, help='Publisher name.') # str
        c.argument('sku_name', id_part=None, help='Name of the Sku.') # str
        c.argument('sku_capacity', id_part=None, help='Capacity of the SKU (number of deployed units of the SKU).') # number
        c.argument('identity', id_part=None, help='Managed service identity of the Api Management service.') # dict
        c.argument('location', id_part=None, help='Resource location.') # str

    with self.argument_context('apimgmt update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('name', id_part=None, help='The name of the API Management service.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('tags', id_part=None, help='Resource tags.') # dictionary
        c.argument('notification_sender_email', id_part=None, help='Email address from which the notification will be sent.') # str
        c.argument('hostname_configurations', id_part=None, help='Custom hostname configuration of the API Management service.') # list
        c.argument('virtual_network_configuration', id_part=None, help='Virtual network configuration of the API Management service.') # dict
        c.argument('additional_locations', id_part=None, help='Additional datacenter locations of the API Management service.') # list
        c.argument('custom_properties', id_part=None, help='Custom properties of the API Management service.</br>Setting `Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Ciphers.TripleDes168` will disable the cipher TLS_RSA_WITH_3DES_EDE_CBC_SHA for all TLS(1.0, 1.1 and 1.2).</br>Setting `Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls11` can be used to disable just TLS 1.1.</br>Setting `Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls10` can be used to disable TLS 1.0 on an API Management service.</br>Setting `Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls11` can be used to disable just TLS 1.1 for communications with backends.</br>Setting `Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls10` can be used to disable TLS 1.0 for communications with backends.</br>Setting `Microsoft.WindowsAzure.ApiManagement.Gateway.Protocols.Server.Http2` can be used to enable HTTP2 protocol on an API Management service.</br>Not specifying any of these properties on PATCH operation will reset omitted properties\' values to their defaults. For all the settings except Http2 the default value is `True` if the service was created on or before April 1st 2018 and `False` otherwise. Http2 setting\'s default value is `False`.') # dictionary
        c.argument('certificates', id_part=None, help='List of Certificates that need to be installed in the API Management service. Max supported certificates that can be installed is 10.') # list
        c.argument('enable_client_certificate', arg_type=get_three_state_flag(), id_part=None, help='Property only meant to be used for Consumption SKU Service. This enforces a client certificate to be presented on each request to the gateway. This also enables the ability to authenticate the certificate in the policy on the gateway.') # boolean
        c.argument('virtual_network_type', id_part=None, help='The type of VPN in which API Management service needs to be configured in. None (Default Value) means the API Management service is not part of any Virtual Network, External means the API Management deployment is set up inside a Virtual Network having an Internet Facing Endpoint, and Internal means that API Management deployment is setup inside a Virtual Network having an Intranet Facing Endpoint only.') # str
        c.argument('publisher_email', id_part=None, help='Publisher email.') # str
        c.argument('publisher_name', id_part=None, help='Publisher name.') # str
        c.argument('sku_name', id_part=None, help='Name of the Sku.') # str
        c.argument('sku_capacity', id_part=None, help='Capacity of the SKU (number of deployed units of the SKU).') # number
        c.argument('identity', id_part=None, help='Managed service identity of the Api Management service.') # dict
        c.argument('location', id_part=None, help='Resource location.') # str

    with self.argument_context('apimgmt delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str

    with self.argument_context('apimgmt show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('name', id_part=None, help='The name of the API Management service.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt diagnostic create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('diagnostic_id', id_part=None, help='Diagnostic identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('always_log', id_part=None, help='Specifies for what type of messages sampling settings should not apply.') # str
        c.argument('logger_id', id_part=None, help='Resource Id of a target logger.') # str
        c.argument('sampling', id_part=None, help='Sampling settings for Diagnostic.') # dict
        c.argument('frontend', id_part=None, help='Diagnostic settings for incoming/outgoing HTTP messages to the Gateway.') # dict
        c.argument('backend', id_part=None, help='Diagnostic settings for incoming/outgoing HTTP messages to the Backend') # dict
        c.argument('enable_http_correlation_headers', arg_type=get_three_state_flag(), id_part=None, help='Whether to process Correlation Headers coming to Api Management Service. Only applicable to Application Insights diagnostics. Default is true.') # boolean

    with self.argument_context('apimgmt diagnostic update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('diagnostic_id', id_part=None, help='Diagnostic identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('always_log', id_part=None, help='Specifies for what type of messages sampling settings should not apply.') # str
        c.argument('logger_id', id_part=None, help='Resource Id of a target logger.') # str
        c.argument('sampling', id_part=None, help='Sampling settings for Diagnostic.') # dict
        c.argument('frontend', id_part=None, help='Diagnostic settings for incoming/outgoing HTTP messages to the Gateway.') # dict
        c.argument('backend', id_part=None, help='Diagnostic settings for incoming/outgoing HTTP messages to the Backend') # dict
        c.argument('enable_http_correlation_headers', arg_type=get_three_state_flag(), id_part=None, help='Whether to process Correlation Headers coming to Api Management Service. Only applicable to Application Insights diagnostics. Default is true.') # boolean

    with self.argument_context('apimgmt diagnostic delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('diagnostic_id', id_part=None, help='Diagnostic identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt diagnostic list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt diagnostic show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('diagnostic_id', id_part=None, help='Diagnostic identifier. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt template create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('name', id_part=None, help='Email Template Name Identifier.') # str
        c.argument('parameters', id_part=None, help='Email Template Parameter values.') # placeholder
        c.argument('subject', id_part=None, help='Subject of the Template.') # str
        c.argument('title', id_part=None, help='Title of the Template.') # str
        c.argument('description', id_part=None, help='Description of the Email Template.') # str
        c.argument('body', id_part=None, help='Email Template Body. This should be a valid XDocument') # str

    with self.argument_context('apimgmt template update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('name', id_part=None, help='Email Template Name Identifier.') # str
        c.argument('parameters', id_part=None, help='Email Template Parameter values.') # placeholder
        c.argument('subject', id_part=None, help='Subject of the Template.') # str
        c.argument('title', id_part=None, help='Title of the Template.') # str
        c.argument('description', id_part=None, help='Description of the Email Template.') # str
        c.argument('body', id_part=None, help='Email Template Body. This should be a valid XDocument') # str

    with self.argument_context('apimgmt template delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('name', id_part=None, help='Email Template Name Identifier.') # str

    with self.argument_context('apimgmt template list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt template show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('name', id_part=None, help='Email Template Name Identifier.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt group create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('group_id', id_part=None, help='Group identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('display_name', id_part=None, help='Group name.') # str
        c.argument('description', id_part=None, help='Group description.') # str
        c.argument('type', id_part=None, help='Group type.') # str
        c.argument('external_id', id_part=None, help='Identifier of the external groups, this property contains the id of the group from the external identity provider, e.g. for Azure Active Directory `aad://<tenant>.onmicrosoft.com/groups/<group object id>`; otherwise the value is null.') # str

    with self.argument_context('apimgmt group update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('group_id', id_part=None, help='Group identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('display_name', id_part=None, help='Group name.') # str
        c.argument('description', id_part=None, help='Group description.') # str
        c.argument('type', id_part=None, help='Group type.') # str
        c.argument('external_id', id_part=None, help='Identifier of the external groups, this property contains the id of the group from the external identity provider, e.g. for Azure Active Directory `aad://<tenant>.onmicrosoft.com/groups/<group object id>`; otherwise the value is null.') # str

    with self.argument_context('apimgmt group delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('group_id', id_part=None, help='Group identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt group list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt group show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('group_id', id_part=None, help='Group identifier. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt group user create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('group_id', id_part=None, help='Group identifier. Must be unique in the current API Management service instance.') # str
        c.argument('user_id', id_part=None, help='User identifier. Must be unique in the current API Management service instance.') # str
        c.argument('state', id_part=None, help='Account state. Specifies whether the user is active or not. Blocked users are unable to sign into the developer portal or call any APIs of subscribed products. Default state is Active.') # str
        c.argument('note', id_part=None, help='Optional note about a user set by the administrator.') # str
        c.argument('identities', id_part=None, help='Collection of user identities.') # list
        c.argument('first_name', id_part=None, help='First name.') # str
        c.argument('last_name', id_part=None, help='Last name.') # str
        c.argument('email', id_part=None, help='Email address.') # str
        c.argument('registration_date', id_part=None, help='Date of user registration. The date conforms to the following format: `yyyy-MM-ddTHH:mm:ssZ` as specified by the ISO 8601 standard.<br>') # datetime
        c.argument('groups', id_part=None, help='Collection of groups user is part of.') # list

    with self.argument_context('apimgmt group user delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('group_id', id_part=None, help='Group identifier. Must be unique in the current API Management service instance.') # str
        c.argument('user_id', id_part=None, help='User identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt group user list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('group_id', id_part=None, help='Group identifier. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt identityprovider create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('name', id_part=None, help='Identity Provider Type identifier.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('type', id_part=None, help='Identity Provider Type identifier.') # str
        c.argument('allowed_tenants', id_part=None, help='List of Allowed Tenants when configuring Azure Active Directory login.') # list
        c.argument('authority', id_part=None, help='OpenID Connect discovery endpoint hostname for AAD or AAD B2C.') # str
        c.argument('signup_policy_name', id_part=None, help='Signup Policy Name. Only applies to AAD B2C Identity Provider.') # str
        c.argument('signin_policy_name', id_part=None, help='Signin Policy Name. Only applies to AAD B2C Identity Provider.') # str
        c.argument('profile_editing_policy_name', id_part=None, help='Profile Editing Policy Name. Only applies to AAD B2C Identity Provider.') # str
        c.argument('password_reset_policy_name', id_part=None, help='Password Reset Policy Name. Only applies to AAD B2C Identity Provider.') # str
        c.argument('client_id', id_part=None, help='Client Id of the Application in the external Identity Provider. It is App ID for Facebook login, Client ID for Google login, App ID for Microsoft.') # str
        c.argument('client_secret', id_part=None, help='Client secret of the Application in external Identity Provider, used to authenticate login request. For example, it is App Secret for Facebook login, API Key for Google login, Public Key for Microsoft.') # str

    with self.argument_context('apimgmt identityprovider update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('name', id_part=None, help='Identity Provider Type identifier.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('type', id_part=None, help='Identity Provider Type identifier.') # str
        c.argument('allowed_tenants', id_part=None, help='List of Allowed Tenants when configuring Azure Active Directory login.') # list
        c.argument('authority', id_part=None, help='OpenID Connect discovery endpoint hostname for AAD or AAD B2C.') # str
        c.argument('signup_policy_name', id_part=None, help='Signup Policy Name. Only applies to AAD B2C Identity Provider.') # str
        c.argument('signin_policy_name', id_part=None, help='Signin Policy Name. Only applies to AAD B2C Identity Provider.') # str
        c.argument('profile_editing_policy_name', id_part=None, help='Profile Editing Policy Name. Only applies to AAD B2C Identity Provider.') # str
        c.argument('password_reset_policy_name', id_part=None, help='Password Reset Policy Name. Only applies to AAD B2C Identity Provider.') # str
        c.argument('client_id', id_part=None, help='Client Id of the Application in the external Identity Provider. It is App ID for Facebook login, Client ID for Google login, App ID for Microsoft.') # str
        c.argument('client_secret', id_part=None, help='Client secret of the Application in external Identity Provider, used to authenticate login request. For example, it is App Secret for Facebook login, API Key for Google login, Public Key for Microsoft.') # str

    with self.argument_context('apimgmt identityprovider delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('name', id_part=None, help='Identity Provider Type identifier.') # str

    with self.argument_context('apimgmt identityprovider list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt identityprovider show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('name', id_part=None, help='Identity Provider Type identifier.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt logger create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('logger_id', id_part=None, help='Logger identifier. Must be unique in the API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('logger_type', id_part=None, help='Logger type.') # str
        c.argument('description', id_part=None, help='Logger description.') # str
        c.argument('credentials', id_part=None, help='The name and SendRule connection string of the event hub for azureEventHub logger.<br>Instrumentation key for applicationInsights logger.') # dictionary
        c.argument('is_buffered', arg_type=get_three_state_flag(), id_part=None, help='Whether records are buffered in the logger before publishing. Default is assumed to be true.') # boolean
        c.argument('resource_id', id_part=None, help='Azure Resource Id of a log target (either Azure Event Hub resource or Azure Application Insights resource).') # str

    with self.argument_context('apimgmt logger update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('logger_id', id_part=None, help='Logger identifier. Must be unique in the API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('logger_type', id_part=None, help='Logger type.') # str
        c.argument('description', id_part=None, help='Logger description.') # str
        c.argument('credentials', id_part=None, help='The name and SendRule connection string of the event hub for azureEventHub logger.<br>Instrumentation key for applicationInsights logger.') # dictionary
        c.argument('is_buffered', arg_type=get_three_state_flag(), id_part=None, help='Whether records are buffered in the logger before publishing. Default is assumed to be true.') # boolean
        c.argument('resource_id', id_part=None, help='Azure Resource Id of a log target (either Azure Event Hub resource or Azure Application Insights resource).') # str

    with self.argument_context('apimgmt logger delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('logger_id', id_part=None, help='Logger identifier. Must be unique in the API Management service instance.') # str

    with self.argument_context('apimgmt logger list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt logger show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('logger_id', id_part=None, help='Logger identifier. Must be unique in the API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt notification create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('name', id_part=None, help='Notification Name Identifier.') # str
        c.argument('title', id_part=None, help='Title of the Notification.') # str
        c.argument('description', id_part=None, help='Description of the Notification.') # str
        c.argument('recipients', id_part=None, help='Recipient Parameter values.') # dict

    with self.argument_context('apimgmt notification update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('name', id_part=None, help='Notification Name Identifier.') # str
        c.argument('title', id_part=None, help='Title of the Notification.') # str
        c.argument('description', id_part=None, help='Description of the Notification.') # str
        c.argument('recipients', id_part=None, help='Recipient Parameter values.') # dict

    with self.argument_context('apimgmt notification list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt notification show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('name', id_part=None, help='Notification Name Identifier.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt notification recipientuser create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('notification_name', id_part=None, help='Notification Name Identifier.') # str
        c.argument('user_id', id_part=None, help='User identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt notification recipientuser update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('notification_name', id_part=None, help='Notification Name Identifier.') # str
        c.argument('user_id', id_part=None, help='User identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt notification recipientuser delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('notification_name', id_part=None, help='Notification Name Identifier.') # str
        c.argument('user_id', id_part=None, help='User identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt notification recipientuser list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('notification_name', id_part=None, help='Notification Name Identifier.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt notification recipientemail create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('notification_name', id_part=None, help='Notification Name Identifier.') # str
        c.argument('email', id_part=None, help='Email identifier.') # str

    with self.argument_context('apimgmt notification recipientemail update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('notification_name', id_part=None, help='Notification Name Identifier.') # str
        c.argument('email', id_part=None, help='Email identifier.') # str

    with self.argument_context('apimgmt notification recipientemail delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('notification_name', id_part=None, help='Notification Name Identifier.') # str
        c.argument('email', id_part=None, help='Email identifier.') # str

    with self.argument_context('apimgmt notification recipientemail list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('notification_name', id_part=None, help='Notification Name Identifier.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt openidconnectprovider create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('opid', id_part=None, help='Identifier of the OpenID Connect Provider.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('display_name', id_part=None, help='User-friendly OpenID Connect Provider name.') # str
        c.argument('description', id_part=None, help='User-friendly description of OpenID Connect Provider.') # str
        c.argument('metadata_endpoint', id_part=None, help='Metadata endpoint URI.') # str
        c.argument('client_id', id_part=None, help='Client ID of developer console which is the client application.') # str
        c.argument('client_secret', id_part=None, help='Client Secret of developer console which is the client application.') # str

    with self.argument_context('apimgmt openidconnectprovider update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('opid', id_part=None, help='Identifier of the OpenID Connect Provider.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('display_name', id_part=None, help='User-friendly OpenID Connect Provider name.') # str
        c.argument('description', id_part=None, help='User-friendly description of OpenID Connect Provider.') # str
        c.argument('metadata_endpoint', id_part=None, help='Metadata endpoint URI.') # str
        c.argument('client_id', id_part=None, help='Client ID of developer console which is the client application.') # str
        c.argument('client_secret', id_part=None, help='Client Secret of developer console which is the client application.') # str

    with self.argument_context('apimgmt openidconnectprovider delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('opid', id_part=None, help='Identifier of the OpenID Connect Provider.') # str

    with self.argument_context('apimgmt openidconnectprovider list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt openidconnectprovider show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('opid', id_part=None, help='Identifier of the OpenID Connect Provider.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt policy create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('value', id_part=None, help='Contents of the Policy as defined by the format.') # str
        c.argument('format', id_part=None, help='Format of the policyContent.') # str

    with self.argument_context('apimgmt policy update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('value', id_part=None, help='Contents of the Policy as defined by the format.') # str
        c.argument('format', id_part=None, help='Format of the policyContent.') # str

    with self.argument_context('apimgmt policy delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str

    with self.argument_context('apimgmt policy list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt policy show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str
        c.argument('format', id_part=None, help='Format of the policyContent.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt portalsetting create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('name', id_part=None, help='The name of the API Management service.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('enabled', arg_type=get_three_state_flag(), id_part=None, help='Redirect Anonymous users to the Sign-In page.') # boolean

    with self.argument_context('apimgmt portalsetting update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('name', id_part=None, help='The name of the API Management service.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('enabled', arg_type=get_three_state_flag(), id_part=None, help='Redirect Anonymous users to the Sign-In page.') # boolean

    with self.argument_context('apimgmt portalsetting show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('name', id_part=None, help='The name of the API Management service.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt portalsetting create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('name', id_part=None, help='The name of the API Management service.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('enabled', arg_type=get_three_state_flag(), id_part=None, help='Allow users to sign up on a developer portal.') # boolean
        c.argument('terms_of_service', id_part=None, help='Terms of service contract properties.') # dict

    with self.argument_context('apimgmt portalsetting update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('name', id_part=None, help='The name of the API Management service.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('enabled', arg_type=get_three_state_flag(), id_part=None, help='Allow users to sign up on a developer portal.') # boolean
        c.argument('terms_of_service', id_part=None, help='Terms of service contract properties.') # dict

    with self.argument_context('apimgmt portalsetting show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('name', id_part=None, help='The name of the API Management service.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt portalsetting create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('name', id_part=None, help='The name of the API Management service.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('url', id_part=None, help='A delegation Url.') # str
        c.argument('validation_key', id_part=None, help='A base64-encoded validation key to validate, that a request is coming from Azure API Management.') # str
        c.argument('subscriptions', id_part=None, help='Subscriptions delegation settings.') # dict
        c.argument('user_registration', id_part=None, help='User registration delegation settings.') # dict

    with self.argument_context('apimgmt portalsetting update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('name', id_part=None, help='The name of the API Management service.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('url', id_part=None, help='A delegation Url.') # str
        c.argument('validation_key', id_part=None, help='A base64-encoded validation key to validate, that a request is coming from Azure API Management.') # str
        c.argument('subscriptions', id_part=None, help='Subscriptions delegation settings.') # dict
        c.argument('user_registration', id_part=None, help='User registration delegation settings.') # dict

    with self.argument_context('apimgmt portalsetting show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('name', id_part=None, help='The name of the API Management service.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt product create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('description', id_part=None, help='Product description. May include HTML formatting tags.') # str
        c.argument('terms', id_part=None, help='Product terms of use. Developers trying to subscribe to the product will be presented and required to accept these terms before they can complete the subscription process.') # str
        c.argument('subscription_required', arg_type=get_three_state_flag(), id_part=None, help='Whether a product subscription is required for accessing APIs included in this product. If true, the product is referred to as "protected" and a valid subscription key is required for a request to an API included in the product to succeed. If false, the product is referred to as "open" and requests to an API included in the product can be made without a subscription key. If property is omitted when creating a new product it\'s value is assumed to be true.') # boolean
        c.argument('approval_required', arg_type=get_three_state_flag(), id_part=None, help='whether subscription approval is required. If false, new subscriptions will be approved automatically enabling developers to call the product’s APIs immediately after subscribing. If true, administrators must manually approve the subscription before the developer can any of the product’s APIs. Can be present only if subscriptionRequired property is present and has a value of false.') # boolean
        c.argument('subscriptions_limit', id_part=None, help='Whether the number of subscriptions a user can have to this product at the same time. Set to null or omit to allow unlimited per user subscriptions. Can be present only if subscriptionRequired property is present and has a value of false.') # number
        c.argument('state', id_part=None, help='whether product is published or not. Published products are discoverable by users of developer portal. Non published products are visible only to administrators. Default state of Product is notPublished.') # str
        c.argument('display_name', id_part=None, help='Product name.') # str

    with self.argument_context('apimgmt product update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('description', id_part=None, help='Product description. May include HTML formatting tags.') # str
        c.argument('terms', id_part=None, help='Product terms of use. Developers trying to subscribe to the product will be presented and required to accept these terms before they can complete the subscription process.') # str
        c.argument('subscription_required', arg_type=get_three_state_flag(), id_part=None, help='Whether a product subscription is required for accessing APIs included in this product. If true, the product is referred to as "protected" and a valid subscription key is required for a request to an API included in the product to succeed. If false, the product is referred to as "open" and requests to an API included in the product can be made without a subscription key. If property is omitted when creating a new product it\'s value is assumed to be true.') # boolean
        c.argument('approval_required', arg_type=get_three_state_flag(), id_part=None, help='whether subscription approval is required. If false, new subscriptions will be approved automatically enabling developers to call the product’s APIs immediately after subscribing. If true, administrators must manually approve the subscription before the developer can any of the product’s APIs. Can be present only if subscriptionRequired property is present and has a value of false.') # boolean
        c.argument('subscriptions_limit', id_part=None, help='Whether the number of subscriptions a user can have to this product at the same time. Set to null or omit to allow unlimited per user subscriptions. Can be present only if subscriptionRequired property is present and has a value of false.') # number
        c.argument('state', id_part=None, help='whether product is published or not. Published products are discoverable by users of developer portal. Non published products are visible only to administrators. Default state of Product is notPublished.') # str
        c.argument('display_name', id_part=None, help='Product name.') # str

    with self.argument_context('apimgmt product delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt product list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt product show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt product api create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('description', id_part=None, help='Description of the API. May include HTML formatting tags.') # str
        c.argument('authentication_settings', id_part=None, help='Collection of authentication settings included into this API.') # dict
        c.argument('subscription_key_parameter_names', id_part=None, help='Protocols over which API is made available.') # dict
        c.argument('type', id_part=None, help='Type of API.') # str
        c.argument('api_revision', id_part=None, help='Describes the Revision of the Api. If no value is provided, default revision 1 is created') # str
        c.argument('api_version', id_part=None, help='Indicates the Version identifier of the API if the API is versioned') # str
        c.argument('is_current', arg_type=get_three_state_flag(), id_part=None, help='Indicates if API revision is current api revision.') # boolean
        c.argument('is_online', arg_type=get_three_state_flag(), id_part=None, help='Indicates if API revision is accessible via the gateway.') # boolean
        c.argument('api_revision_description', id_part=None, help='Description of the Api Revision.') # str
        c.argument('api_version_description', id_part=None, help='Description of the Api Version.') # str
        c.argument('api_version_set_id', id_part=None, help='A resource identifier for the related ApiVersionSet.') # str
        c.argument('subscription_required', arg_type=get_three_state_flag(), id_part=None, help='Specifies whether an API or Product subscription is required for accessing the API.') # boolean
        c.argument('source_api_id', id_part=None, help='API identifier of the source API.') # str
        c.argument('display_name', id_part=None, help='API name. Must be 1 to 300 characters long.') # str
        c.argument('service_url', id_part=None, help='Absolute URL of the backend service implementing this API. Cannot be more than 2000 characters long.') # str
        c.argument('path', id_part=None, help='Relative URL uniquely identifying this API and all of its resource paths within the API Management service instance. It is appended to the API endpoint base URL specified during the service instance creation to form a public URL for this API.') # str
        c.argument('protocols', id_part=None, help='Describes on which protocols the operations in this API can be invoked.') # list
        c.argument('api_version_set', id_part=None, help='Version set details') # dict

    with self.argument_context('apimgmt product api update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str
        c.argument('description', id_part=None, help='Description of the API. May include HTML formatting tags.') # str
        c.argument('authentication_settings', id_part=None, help='Collection of authentication settings included into this API.') # dict
        c.argument('subscription_key_parameter_names', id_part=None, help='Protocols over which API is made available.') # dict
        c.argument('type', id_part=None, help='Type of API.') # str
        c.argument('api_revision', id_part=None, help='Describes the Revision of the Api. If no value is provided, default revision 1 is created') # str
        c.argument('api_version', id_part=None, help='Indicates the Version identifier of the API if the API is versioned') # str
        c.argument('is_current', arg_type=get_three_state_flag(), id_part=None, help='Indicates if API revision is current api revision.') # boolean
        c.argument('is_online', arg_type=get_three_state_flag(), id_part=None, help='Indicates if API revision is accessible via the gateway.') # boolean
        c.argument('api_revision_description', id_part=None, help='Description of the Api Revision.') # str
        c.argument('api_version_description', id_part=None, help='Description of the Api Version.') # str
        c.argument('api_version_set_id', id_part=None, help='A resource identifier for the related ApiVersionSet.') # str
        c.argument('subscription_required', arg_type=get_three_state_flag(), id_part=None, help='Specifies whether an API or Product subscription is required for accessing the API.') # boolean
        c.argument('source_api_id', id_part=None, help='API identifier of the source API.') # str
        c.argument('display_name', id_part=None, help='API name. Must be 1 to 300 characters long.') # str
        c.argument('service_url', id_part=None, help='Absolute URL of the backend service implementing this API. Cannot be more than 2000 characters long.') # str
        c.argument('path', id_part=None, help='Relative URL uniquely identifying this API and all of its resource paths within the API Management service instance. It is appended to the API endpoint base URL specified during the service instance creation to form a public URL for this API.') # str
        c.argument('protocols', id_part=None, help='Describes on which protocols the operations in this API can be invoked.') # list
        c.argument('api_version_set', id_part=None, help='Version set details') # dict

    with self.argument_context('apimgmt product api delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str
        c.argument('api_id', id_part=None, help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.') # str

    with self.argument_context('apimgmt product api list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt product group create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str
        c.argument('group_id', id_part=None, help='Group identifier. Must be unique in the current API Management service instance.') # str
        c.argument('display_name', id_part=None, help='Group name.') # str
        c.argument('description', id_part=None, help='Group description. Can contain HTML formatting tags.') # str
        c.argument('built_in', arg_type=get_three_state_flag(), id_part=None, help='true if the group is one of the three system groups (Administrators, Developers, or Guests); otherwise false.') # boolean
        c.argument('type', id_part=None, help='Group type.') # str
        c.argument('external_id', id_part=None, help='For external groups, this property contains the id of the group from the external identity provider, e.g. for Azure Active Directory `aad://<tenant>.onmicrosoft.com/groups/<group object id>`; otherwise the value is null.') # str

    with self.argument_context('apimgmt product group update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str
        c.argument('group_id', id_part=None, help='Group identifier. Must be unique in the current API Management service instance.') # str
        c.argument('display_name', id_part=None, help='Group name.') # str
        c.argument('description', id_part=None, help='Group description. Can contain HTML formatting tags.') # str
        c.argument('built_in', arg_type=get_three_state_flag(), id_part=None, help='true if the group is one of the three system groups (Administrators, Developers, or Guests); otherwise false.') # boolean
        c.argument('type', id_part=None, help='Group type.') # str
        c.argument('external_id', id_part=None, help='For external groups, this property contains the id of the group from the external identity provider, e.g. for Azure Active Directory `aad://<tenant>.onmicrosoft.com/groups/<group object id>`; otherwise the value is null.') # str

    with self.argument_context('apimgmt product group delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str
        c.argument('group_id', id_part=None, help='Group identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt product group list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt product policy create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('value', id_part=None, help='Contents of the Policy as defined by the format.') # str
        c.argument('format', id_part=None, help='Format of the policyContent.') # str

    with self.argument_context('apimgmt product policy update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('value', id_part=None, help='Contents of the Policy as defined by the format.') # str
        c.argument('format', id_part=None, help='Format of the policyContent.') # str

    with self.argument_context('apimgmt product policy delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str

    with self.argument_context('apimgmt product policy list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt product policy show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('product_id', id_part=None, help='Product identifier. Must be unique in the current API Management service instance.') # str
        c.argument('policy_id', id_part=None, help='The identifier of the Policy.') # str
        c.argument('format', id_part=None, help='Format of the policyContent.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt property create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('prop_id', id_part=None, help='Identifier of the property.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('tags', id_part=None, help='Optional tags that when provided can be used to filter the property list.') # list
        c.argument('secret', arg_type=get_three_state_flag(), id_part=None, help='Determines whether the value is a secret and should be encrypted or not. Default value is false.') # boolean
        c.argument('display_name', id_part=None, help='Unique name of Property. It may contain only letters, digits, period, dash, and underscore characters.') # str
        c.argument('value', id_part=None, help='Value of the property. Can contain policy expressions. It may not be empty or consist only of whitespace.') # str

    with self.argument_context('apimgmt property update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('prop_id', id_part=None, help='Identifier of the property.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('tags', id_part=None, help='Optional tags that when provided can be used to filter the property list.') # list
        c.argument('secret', arg_type=get_three_state_flag(), id_part=None, help='Determines whether the value is a secret and should be encrypted or not. Default value is false.') # boolean
        c.argument('display_name', id_part=None, help='Unique name of Property. It may contain only letters, digits, period, dash, and underscore characters.') # str
        c.argument('value', id_part=None, help='Value of the property. Can contain policy expressions. It may not be empty or consist only of whitespace.') # str

    with self.argument_context('apimgmt property delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('prop_id', id_part=None, help='Identifier of the property.') # str

    with self.argument_context('apimgmt property list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt property show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('prop_id', id_part=None, help='Identifier of the property.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt subscription create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('sid', id_part=None, help='Subscription entity Identifier. The entity represents the association between a user and a product in API Management.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('notify', arg_type=get_three_state_flag(), id_part=None, help='Notify change in Subscription State. <br> - If false, do not send any email notification for change of state of subscription <br> - If true, send email notification of change of state of subscription ') # boolean
        c.argument('owner_id', id_part=None, help='User (user id path) for whom subscription is being created in form /users/{userId}') # str
        c.argument('scope', id_part=None, help='Scope like /products/{productId} or /apis or /apis/{apiId}.') # str
        c.argument('display_name', id_part=None, help='Subscription name.') # str
        c.argument('primary_key', id_part=None, help='Primary subscription key. If not specified during request key will be generated automatically.') # str
        c.argument('secondary_key', id_part=None, help='Secondary subscription key. If not specified during request key will be generated automatically.') # str
        c.argument('state', id_part=None, help='Initial subscription state. If no value is specified, subscription is created with Submitted state. Possible states are * active – the subscription is active, * suspended – the subscription is blocked, and the subscriber cannot call any APIs of the product, * submitted – the subscription request has been made by the developer, but has not yet been approved or rejected, * rejected – the subscription request has been denied by an administrator, * cancelled – the subscription has been cancelled by the developer or administrator, * expired – the subscription reached its expiration date and was deactivated.') # str
        c.argument('allow_tracing', arg_type=get_three_state_flag(), id_part=None, help='Determines whether tracing can be enabled') # boolean

    with self.argument_context('apimgmt subscription update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('sid', id_part=None, help='Subscription entity Identifier. The entity represents the association between a user and a product in API Management.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('notify', arg_type=get_three_state_flag(), id_part=None, help='Notify change in Subscription State. <br> - If false, do not send any email notification for change of state of subscription <br> - If true, send email notification of change of state of subscription ') # boolean
        c.argument('owner_id', id_part=None, help='User (user id path) for whom subscription is being created in form /users/{userId}') # str
        c.argument('scope', id_part=None, help='Scope like /products/{productId} or /apis or /apis/{apiId}.') # str
        c.argument('display_name', id_part=None, help='Subscription name.') # str
        c.argument('primary_key', id_part=None, help='Primary subscription key. If not specified during request key will be generated automatically.') # str
        c.argument('secondary_key', id_part=None, help='Secondary subscription key. If not specified during request key will be generated automatically.') # str
        c.argument('state', id_part=None, help='Initial subscription state. If no value is specified, subscription is created with Submitted state. Possible states are * active – the subscription is active, * suspended – the subscription is blocked, and the subscriber cannot call any APIs of the product, * submitted – the subscription request has been made by the developer, but has not yet been approved or rejected, * rejected – the subscription request has been denied by an administrator, * cancelled – the subscription has been cancelled by the developer or administrator, * expired – the subscription reached its expiration date and was deactivated.') # str
        c.argument('allow_tracing', arg_type=get_three_state_flag(), id_part=None, help='Determines whether tracing can be enabled') # boolean

    with self.argument_context('apimgmt subscription delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('sid', id_part=None, help='Subscription entity Identifier. The entity represents the association between a user and a product in API Management.') # str

    with self.argument_context('apimgmt subscription list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt subscription show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('sid', id_part=None, help='Subscription entity Identifier. The entity represents the association between a user and a product in API Management.') # str
    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


    with self.argument_context('apimgmt user create') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('user_id', id_part=None, help='User identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('state', id_part=None, help='Account state. Specifies whether the user is active or not. Blocked users are unable to sign into the developer portal or call any APIs of subscribed products. Default state is Active.') # str
        c.argument('note', id_part=None, help='Optional note about a user set by the administrator.') # str
        c.argument('identities', id_part=None, help='Collection of user identities.') # list
        c.argument('email', id_part=None, help='Email address. Must not be empty and must be unique within the service instance.') # str
        c.argument('first_name', id_part=None, help='First name.') # str
        c.argument('last_name', id_part=None, help='Last name.') # str
        c.argument('password', id_part=None, help='User Password. If no value is provided, a default password is generated.') # str
        c.argument('confirmation', id_part=None, help='Determines the type of confirmation e-mail that will be sent to the newly created user.') # str

    with self.argument_context('apimgmt user update') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('user_id', id_part=None, help='User identifier. Must be unique in the current API Management service instance.') # str
        c.argument('parameters', id_part=None, help='undefined') # placeholder
        c.argument('state', id_part=None, help='Account state. Specifies whether the user is active or not. Blocked users are unable to sign into the developer portal or call any APIs of subscribed products. Default state is Active.') # str
        c.argument('note', id_part=None, help='Optional note about a user set by the administrator.') # str
        c.argument('identities', id_part=None, help='Collection of user identities.') # list
        c.argument('email', id_part=None, help='Email address. Must not be empty and must be unique within the service instance.') # str
        c.argument('first_name', id_part=None, help='First name.') # str
        c.argument('last_name', id_part=None, help='Last name.') # str
        c.argument('password', id_part=None, help='User Password. If no value is provided, a default password is generated.') # str
        c.argument('confirmation', id_part=None, help='Determines the type of confirmation e-mail that will be sent to the newly created user.') # str

    with self.argument_context('apimgmt user delete') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('user_id', id_part=None, help='User identifier. Must be unique in the current API Management service instance.') # str

    with self.argument_context('apimgmt user list') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str

    with self.argument_context('apimgmt user show') as c:
        c.argument('resource_group', id_part=None, help='The name of the resource group.') # str
        c.argument('service_name', id_part=None, help='The name of the API Management service.') # str
        c.argument('user_id', id_part=None, help='User identifier. Must be unique in the current API Management service instance.') # str
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimanagement') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimanagement_name', name_arg_type, options_list=['--name', '-n'])