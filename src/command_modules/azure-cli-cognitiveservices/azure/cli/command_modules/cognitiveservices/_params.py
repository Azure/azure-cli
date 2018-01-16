# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (
    tags_type,
    resource_group_name_type,
    get_resource_name_completion_list)


name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME')


def load_arguments(self, _):
    with self.argument_context('cognitiveservices') as c:
        c.argument('account_name', arg_type=name_arg_type, help='cognitive service account name',
                   completer=get_resource_name_completion_list('Microsoft.CognitiveServices/accounts'))
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('sku_name', options_list=['--sku'], help='the Sku of cognitive services account')
        c.argument('kind', help='the API name of cognitive services account')
        c.argument('tags', tags_type)
        c.argument('key_name', required=True, help='Key name to generate', choices=['key1', 'key2'])

    with self.argument_context('cognitiveservices account create') as c:
        c.argument('yes', action='store_true', help='Do not prompt for terms confirmation')
