# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from enum import Enum
from azure.cli.core.commands.parameters import (get_enum_type,
                                                get_location_type,
                                                resource_group_name_type,
                                                get_three_state_flag)

from azure.mgmt.apimanagement.models import (SkuType, VirtualNetworkType, Protocol, ApiType)


SKU_TYPES = SkuType
VNET_TYPES = VirtualNetworkType
API_PROTOCOLS = Protocol
API_TYPES = ApiType


class ImportFormat(Enum):
    Wadl = "Wadl"
    Swagger = "Swagger"
    OpenApi = "OpenApi"
    OpenApiJson = "OpenApiJson"
    Wsdl = "Wsdl"


def load_arguments(self, _):

    from azure.cli.core.commands.parameters import tags_type
    from azure.cli.core.commands.validators import get_default_location_from_resource_group

    with self.argument_context('apim') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('tags', tags_type)
        c.argument('service_name', options_list=['--name', '-n'], help="The name of the api management service instance", id_part=None)
        c.argument('name', options_list=['--name', '-n'], help="The name of the api management service instance", id_part=None)
        c.argument('location', validator=get_default_location_from_resource_group)

    with self.argument_context('apim create') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('publisher_name', help='The name of your organization for use in the developer portal and e-mail notifications.', required=True)
        c.argument('publisher_email', help='The e-mail address to receive all system notifications.')
        c.argument('enable_client_certificate', arg_type=get_three_state_flag(), help='Enforces a client certificate to be presented on each request to the gateway and also enables the ability to authenticate the certificate in the policy on the gateway.')
        c.argument('virtual_network_type', get_enum_type(VNET_TYPES), options_list=['--virtual-network', '-v'], help='The virtual network type.')
        c.argument('sku_name', arg_type=get_enum_type(SKU_TYPES), help='The sku of the api management instance')
        c.argument('sku_capacity', type=int, help='The number of deployed units of the SKU.')
        c.argument('enable_managed_identity', arg_type=get_three_state_flag(), help='Create a managed identity for the API Management service to access other Azure resources.')

    with self.argument_context('apim update') as c:
        c.argument('publisher_name', help='The name of your organization for use in the developer portal and e-mail notifications.')
        c.argument('publisher_email', help='The e-mail address to receive all system notifications.')
        c.argument('enable_client_certificate', arg_type=get_three_state_flag(), help='Enforces a client certificate to be presented on each request to the gateway and also enables the ability to authenticate the certificate in the policy on the gateway.')
        c.argument('virtual_network_type', get_enum_type(VNET_TYPES), options_list=['--virtual-network', '-v'], help='The virtual network type.')
        c.argument('sku_name', arg_type=get_enum_type(SKU_TYPES), help='The sku of the api management instance')
        c.argument('sku_capacity', type=int, help='The number of deployed units of the SKU.')
        c.argument('enable_managed_identity', arg_type=get_three_state_flag(), help='Create a managed identity for the API Management service to access other Azure resources.')

    with self.argument_context('apim backup') as c:
        c.argument('backup_name', help='The name of the backup file to create.')
        c.argument('storage_account_name', arg_group='Storage', help='The name of the storage account used to place the backup.')
        c.argument('storage_account_key', arg_group='Storage', help='The access key of the storage account used to place the backup.')
        c.argument('storage_account_container', arg_group='Storage', help='The name of the storage account container used to place the backup.')

    with self.argument_context('apim api show') as c:
        c.argument('service_name', options_list=['--service-name'], help='The name of the API Management service instance.')
        c.argument('api_id', arg_group='API', help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.')

    with self.argument_context('apim api list') as c:
        c.argument('service_name', options_list=['--service-name', '-n'], help='The name of the API Management service instance.')
        c.argument('filter_display_name', arg_group='API', help='Filter of APIs by displayName.')
        c.argument('skip', type=int, help='Number of records to skip.')
        c.argument('top', type=int, help='Number of records to return.')

    with self.argument_context('apim api create') as c:
        c.argument('service_name', options_list=['--service-name', '-n'], help='The name of the API Management service instance.')
        c.argument('api_id', arg_group='API', help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.', required=True)
        c.argument('path', arg_group='API', help='Required. Relative URL uniquely identifying this API and all of its resource paths within the API Management service instance.', required=True)
        c.argument('display_name', arg_group='API', help='API name. Must be 1 to 300 characters long.', required=True)
        c.argument('description', arg_group='API', help='Description of the API. May include HTML formatting tags.')
        c.argument('subscription_key_header_name', arg_group='API', help='Specifies the subscription key header name.')
        c.argument('subscription_key_query_param_name', arg_group='API', help='Specifies the subscription key query string parameter name.')
        c.argument('open_id_provider_id', help='Specifies the openid in the authentication setting.')
        c.argument('bearer_token_sending_methods', nargs='+', help='Specifies the sending methods for bearer token.')
        c.argument('authorization_server_id', help='Specifies the OAuth authorization server ID.')
        c.argument('authorization_scope', help='Specifies the OAuth operations scope.')
        c.argument('service_url', arg_group='API', help='Absolute URL of the backend service implementing this API. Cannot be more than 2000 characters long.')
        c.argument('protocols', arg_group='API', arg_type=get_enum_type(API_PROTOCOLS), nargs='+', help='Describes on which protocols the operations in this API can be invoked.')
        c.argument('api_type', arg_group='API', arg_type=get_enum_type(API_TYPES), help='The type of the API.')
        c.argument('subscription_required', arg_group='API', arg_type=get_three_state_flag(), help='If true, the API requires a subscription key on requests.')
        c.argument('subscription_key_required', help='Specifies whether subscription key is required during call to this API, true - API is included into closed products only, false - API is included into open products alone, null - there is a mix of products.')
        c.argument('tags', tags_type)

    with self.argument_context('apim api delete') as c:
        c.argument('service_name', options_list=['--service-name', '-n'], help='The name of the API Management service instance.')
        c.argument('api_id', arg_group='API', help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.')
        c.argument('delete_revisions', help='Delete all revisions of the Api.')
        c.argument('if_match', help='ETag of the Entity.')

    with self.argument_context('apim api update') as c:
        c.argument('service_name', options_list=['--service-name', '-n'], help='The name of the API Management service instance.')
        c.argument('api_id', arg_group='API', help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.', required=True)
        c.argument('display_name', arg_group='API', help='API name. Must be 1 to 300 characters long.')
        c.argument('path', arg_group='API', help='Required. Relative URL uniquely identifying this API and all of its resource paths within the API Management service instance.')
        c.argument('description', arg_group='API', help='Description of the API. May include HTML formatting tags.')
        c.argument('subscription_key_header_name', arg_group='API', help='Specifies the subscription key header name.')
        c.argument('subscription_key_query_param_name', arg_group='API', help='Specifies the subscription key query string parameter name.')
        c.argument('service_url', arg_group='API', help='Absolute URL of the backend service implementing this API. Cannot be more than 2000 characters long.')
        c.argument('protocols', arg_group='API', arg_type=get_enum_type(API_PROTOCOLS), nargs='+', help='Describes on which protocols the operations in this API can be invoked.')
        c.argument('api_type', arg_group='API', arg_type=get_enum_type(API_TYPES), help='The type of the API.')
        c.argument('subscription_required', arg_group='API', arg_type=get_three_state_flag(), help='If true, the API requires a subscription key on requests.')
        c.argument('tags', tags_type)

    with self.argument_context('apim api import') as c:
        c.argument('service_name', options_list=['--service-name', '-n'], help="The name of the api management service instance", id_part=None)
        c.argument('path', arg_group='API', help='Required. Relative URL uniquely identifying this API and all of its resource paths within the API Management service instance.', required=True)
        c.argument('description', arg_group='API', help='Description of the API. May include HTML formatting tags.')
        c.argument('subscription_key_header_name', arg_group='API', help='Specifies the subscription key header name.')
        c.argument('subscription_key_query_param_name', arg_group='API', help='Specifies the subscription key query string parameter name.')
        c.argument('api_id', arg_group='API', help='API revision identifier. Must be unique in the current API Management service instance. Non-current revision has ;rev=n as a suffix where n is the revision number.')
        c.argument('api_revision', arg_group='API', help='Describes the Revision of the Api. If no value is provided, default revision 1 is created.')
        c.argument('service_url', arg_group='API', help='Absolute URL of the backend service implementing this API. Cannot be more than 2000 characters long.')
        c.argument('protocols', arg_group='API', arg_type=get_enum_type(API_PROTOCOLS), nargs='+', help='Describes on which protocols the operations in this API can be invoked.')
        c.argument('api_type', arg_group='API', arg_type=get_enum_type(API_TYPES), help='The type of the API.')
        c.argument('subscription_required', arg_group='API', arg_type=get_three_state_flag(), help='If true, the API requires a subscription key on requests.')
        c.argument('display_name', arg_group='API', help='Display name of this API.')
        c.argument('specification_path', help='File path specified to import the API.')
        c.argument('specification_url', help='Url specified to import the API.')
        c.argument('specification_format', arg_type=get_enum_type(ImportFormat), help='Specify the format of the imported API.')
        c.argument('soap_api_type', help='The type of API when file format is WSDL.')
        c.argument('wsdl_service_name', help='Local name of WSDL Service to be imported.')
        c.argument('wsdl_endpoint_name', help='Local name of WSDL Endpoint (port) to be imported.')
