# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import argparse
from azure.cli.core.commands.parameters import resource_group_name_type, tags_type
from knack.arguments import CLIArgumentType

def load_arguments(self, _):

    name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME')


    with self.argument_context('dms') as c:
        c.argument('service_name', name_arg_type, help='The name of the Service')
        c.argument('group_name', resource_group_name_type)


    with self.argument_context('dms project') as c:
        c.argument('service_name', options_list=['--service-name'])
        c.argument('project_name', name_arg_type, help='The name of the Project')
        c.argument('database_list', nargs='*', help='A space delimited list of databases')


    with self.argument_context('dms project task') as c:
        c.argument('service_name', options_list=['--service-name'])
        c.argument('project_name', options_list=['--project-name'])
        c.argument('task_name', name_arg_type, help='The name of the Task')