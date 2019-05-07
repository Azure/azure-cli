# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.validators import get_default_location_from_resource_group


def load_arguments(self, _):
    with self.argument_context('network nat-gateway') as c:
        c.argument('nat_gateway_name',
                   id_part='name',
                   options_list=['--name', '-n'],
                   help='The name of the nat gateway')
        c.argument('location', validator=get_default_location_from_resource_group)
        c.ignore('expand')
