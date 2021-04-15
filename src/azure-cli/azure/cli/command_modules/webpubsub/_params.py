# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType
from azure.mgmt.webpubsub.models import WebPubSubRequestType
from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    get_location_type,
    get_resource_name_completion_list,
    tags_type,
    get_enum_type,
    get_three_state_flag
)

WEBPUBSUB_KEY_TYPE = ['primary', 'secondary']

def load_arguments(self, _):

    from azure.cli.core.commands.parameters import tags_type
    from azure.cli.core.commands.validators import get_default_location_from_resource_group

    webpubsub_name_type = CLIArgumentType(options_list='--webpubsub-name-name', help='Name of the Webpubsub.', id_part='name')

    with self.argument_context('webpubsub') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('webpubsub_name', webpubsub_name_type, options_list=['--name', '-n'])

    with self.argument_context('webpubsub list') as c:
        c.argument('webpubsub_name', webpubsub_name_type, id_part=None)

    with self.argument_context('webpubsub create') as c:
        c.argument('sku', help='The sku name of the signalr service. E.g. Standard_S1, Free_F1')
        c.argument('unit_count', help='The number of signalr service unit count', type=int)

    with self.argument_context('webpubsub update') as c:
        c.argument('sku', help='The sku name of the signalr service. E.g. Standard_S1, Free_F1')
        c.argument('unit_count', help='The number of signalr service unit count', type=int)

    with self.argument_context('webpubsub key regenerate') as c:
        c.argument('key_type', help='The name of access key to regenerate', choices=WEBPUBSUB_KEY_TYPE)

    # Network Rule
    with self.argument_context('webpubsub network-rule update') as c:
        c.argument('connection_name', nargs='*', help='Space-separeted list of private endpoint connection name.', required=False, arg_group='Private Endpoint Connection')
        c.argument('public_network', arg_type=get_three_state_flag(), help='Set rules for public network.', required=False, arg_group='Public Network')
        c.argument('allow', nargs='*', help='The allowed virtual network rule. Space-separeted list of scope to assign. Allowed values: ClientConnection, ServerConnection, RESTAPI, Trace', type=WebPubSubRequestType, required=False)
        c.argument('deny', nargs='*', help='The denied virtual network rule. Space-separeted list of scope to assign. Allowed values: ClientConnection, ServerConnection, RESTAPI, Trace', type=WebPubSubRequestType, required=False)

    with self.argument_context('webpubsub event-handler update') as c:
        c.argument('items', help='A JSON-formatted string containing event handler items')