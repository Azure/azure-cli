# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import argparse

from knack.arguments import CLIArgumentType

def load_arguments(self, _):

    from azure.cli.core.commands.parameters import resource_group_name_type, tags_type

    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')
    list_arg_type = CLIArgumentType(nargs='*')

    # region Global

    with self.argument_context('dms') as c:
        c.argument('service_name', name_arg_type, help='The name of the Service')
        c.argument('group_name', resource_group_name_type)
        c.argument('tags', tags_type)

    with self.argument_context('dms create') as c:
        #c.argument('ids', CLIArgumentType(options_list=('--vnet-subnet-ids')))
        c.argument('vnet_name', id_part='name')
        c.argument('vnet_resource_group_name', id_part='resource_group')
        c.argument('subnet_name', id_part='child_name_1')

    # endregion

    # region Project

    with self.argument_context('dms project') as c:
        c.argument('database_list', list_arg_type)
        #c.argument('project_name', name_arg_type, help='The name of the Project')

    # endregion