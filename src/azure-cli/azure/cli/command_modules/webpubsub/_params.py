# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType


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