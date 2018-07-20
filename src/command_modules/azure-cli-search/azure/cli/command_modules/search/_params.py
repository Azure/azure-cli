# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands.parameters import name_type


def load_arguments(self, _):
    with self.argument_context('search service') as c:
        c.argument('search_service_name', arg_type=name_type, help='The name of the search service.')

    with self.argument_context('search query-key') as c:
        c.argument('name', options_list=['--name', '-n'], help='The name of the query key.')
        c.argument('key', options_list=['--key', '--key-value'], help='The value of the query key.')

    with self.argument_context('search admin-key') as c:
        c.argument('key_kind', options_list=['--key', '--key-kind'],
                   help='The type (primary or secondary) of the admin key.')
