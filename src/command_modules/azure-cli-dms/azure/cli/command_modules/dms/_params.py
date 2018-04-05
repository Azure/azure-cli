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
        #c.argument('service_name', name_arg_type)
        c.argument('service_name', help='The name of the Service')
        c.argument('group_name', resource_group_name_type)
        c.argument('tags', tags_type)

    for item in ['check-name-availability', 'check-status', 'create', 'delete', 'show', 'start', 'stop']:
        with self.argument_context('dms {}'.format(item)) as c:
            c.argument('service_name', name_arg_type)

    with self.argument_context('dms wait') as c:
        c.argument('service_name', name_arg_type, id_part='name')

    # endregion

    # region Project

    with self.argument_context('dms project') as c:
        #c.argument('service-name', options_list=['--service-name'])
        c.argument('project_name', name_arg_type, help='The name of the Project')
        c.argument('database_list', nargs='*', help='A space delimited list of databases')

    # endregion

    # region Task

    with self.argument_context('dms task') as c:
        c.argument('task_name', name_arg_type, help='The name of the Task')

    # endregion