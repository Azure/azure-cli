# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands.parameters import get_enum_type, get_three_state_flag


def load_arguments(self, _):

    with self.argument_context('configure') as c:
        c.argument('defaults', nargs='+', options_list=('--defaults', '-d'))
        c.argument('list_defaults', options_list=('--list-defaults', '-l'),
                   arg_type=get_three_state_flag(), help='list all applicable defaults')
        c.argument('scope', arg_type=get_enum_type(['global', 'local']), default='global',
                   help='scope of defaults. Using "local" for settings only effective under current folder')
        c.ignore('_subscription')  # ignore the global subscription param

    with self.argument_context('cache') as c:
        c.argument('resource_type', options_list=['--resource-type', '-t'], help='The resource type.')
        c.argument('item_name', options_list=['--name', '-n'], help='The resource name.')
