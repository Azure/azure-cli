# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands.parameters import name_type, get_enum_type


def load_arguments(self, _):
    with self.argument_context('search service') as c:
        c.ignore('search_management_request_options')
        c.argument('search_service_name', arg_type=name_type, help='The name of the search service.')

    with self.argument_context('search service create') as c:
        c.ignore('search_management_request_options')
        c.argument('sku', help='Search Service SKU', arg_type=get_enum_type(["Free", "Basic", "Standard", "Standard2", "Standard3"]))
        c.argument('public_network_access', options_list=['--public-network-access', '--public-access'])

    with self.argument_context('search service update') as c:
        c.ignore('search_management_request_options')
        c.argument('public_network_access', options_list=['--public-network-access', '--public-access'])

    with self.argument_context('search privateendpointconnection') as c:
        c.ignore('search_management_request_options')
        c.argument('search_service_name', options_list=['--service-name'], help='The name of the search service.')

    with self.argument_context('search privateendpointconnection update') as c:
        c.ignore('search_management_request_options')
        c.argument('private_endpoint_connection_name', options_list=['--name'])
        c.argument('private_link_service_connection_actions_required', options_list=['--actions-required'])
        c.argument('private_link_service_connection_description', options_list=['--description'])
        c.argument('private_link_service_connection_status', options_list=['--status'])

    with self.argument_context('search privateendpointconnection show') as c:
        c.ignore('search_management_request_options')
        c.argument('private_endpoint_connection_name', options_list=['--private-endpoint-connection-name', '--name'])

    with self.argument_context('search privateendpointconnection delete') as c:
        c.ignore('search_management_request_options')
        c.argument('private_endpoint_connection_name', options_list=['--private-endpoint-connection-name', '--name'])

    with self.argument_context('search privatelinkresource') as c:
        c.ignore('search_management_request_options')
        c.argument('search_service_name', options_list=['--service-name'], help='The name of the search service.')

    with self.argument_context('search sharedprivatelinkresource') as c:
        c.ignore('search_management_request_options')
        c.argument('search_service_name', options_list=['--service-name'], help='The name of the search service.')
        c.argument('shared_private_link_resource_name', options_list=['--name'])

    with self.argument_context('search sharedprivatelinkresource createorupdate') as c:
        c.ignore('search_management_request_options')
        c.argument('shared_private_link_resource_group_id', options_list=['--group-id'])
        c.argument('shared_private_link_resource_id', options_list=['--id'])
        c.argument('shared_private_link_resource_request_message', options_list=['--request-message'])

    with self.argument_context('search query-key') as c:
        c.ignore('search_management_request_options')
        c.argument('search_service_name', options_list=['--service-name'], help='The name of the search service.')
        c.argument('name', options_list=['--name', '-n'], help='The name of the query key.')
        c.argument('key', options_list=['--key-value'], help='The value of the query key.')

    with self.argument_context('search admin-key') as c:
        c.ignore('search_management_request_options')
        c.argument('search_service_name', options_list=['--service-name'], help='The name of the search service.')
        c.argument('key_kind', options_list=['--key-kind'],
                   help='The type (primary or secondary) of the admin key.')
