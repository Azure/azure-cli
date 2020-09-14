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

    with self.argument_context('local-context off') as c:
        c.argument('yes', options_list=['--yes', '-y'], help='Do not prompt for confirmation.', action='store_true')

    with self.argument_context('local-context show') as c:
        c.argument('name', nargs='+', options_list=['--name', '-n'], help='Space-separated list of local context parameter names.')

    with self.argument_context('local-context delete') as c:
        c.argument('name', nargs='+', options_list=['--name', '-n'], help='Space-separated list of local context parameter names. Either --name or --all can be specified.')
        c.argument('all', help='Clear all local context data. Either --name or --all can be specified.', action='store_true')
        c.argument('yes', options_list=['--yes', '-y'], help='Do not prompt for confirmation. Only available when --all is specified.', action='store_true')
        c.argument('purge', help='Delete local context file from working directory. Only available when --all is specified.', action='store_true')
        c.argument('recursive', help='Indicate this is recursive delete of local context. Only available when --all is specified.', action='store_true')
