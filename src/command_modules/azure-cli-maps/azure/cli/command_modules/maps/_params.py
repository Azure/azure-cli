# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (
    get_enum_type,
    get_resource_name_completion_list,
    resource_group_name_type,
    tags_type)

from azure.mgmt.maps.models import KeyType


def load_arguments(self, _):
    # Argument Definition
    maps_name_type = CLIArgumentType(options_list=['--name', '-n'],
                                     completer=get_resource_name_completion_list('Microsoft.Maps/accounts'),
                                     help='The name of the maps account')

    # Parameter Registration
    with self.argument_context('maps') as c:
        c.argument('resource_group_name',
                   arg_type=resource_group_name_type,
                   id_part='resource_group',
                   help='Resource group name')
        c.argument('account_name',
                   id_part='name',
                   arg_type=maps_name_type)

    with self.argument_context('maps account') as c:
        c.argument('sku_name',
                   options_list=['--sku', '-s'],
                   help='The name of the SKU.',
                   arg_type=get_enum_type(['S0', 'S1']))
        c.argument('tags',
                   arg_type=tags_type)

    with self.argument_context('maps account create') as c:
        c.argument('force',
                   options_list=['--accept-tos'],
                   action='store_true')

    # Prevent --ids argument in keys with id_part=None
    with self.argument_context('maps account keys') as c:
        c.argument('account_name',
                   id_part=None,
                   arg_type=maps_name_type)

    with self.argument_context('maps account keys renew') as c:
        c.argument('key_type',
                   options_list=['--key'],
                   arg_type=get_enum_type(KeyType))
