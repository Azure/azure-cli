# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import resource_group_name_type, tags_type


def load_arguments(self, _):

    name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME')

    with self.argument_context('dms') as c:
        c.argument('service_name', name_arg_type, help='The name of the Service.')
        c.argument('group_name', resource_group_name_type)
        c.argument('tags', tags_type, help='A space-delimited list of tags in "tag1[=value1]" format.')

    with self.argument_context('dms project') as c:
        c.argument('service_name', options_list=['--service-name'])
        c.argument('project_name', name_arg_type, help='The name of the Project.')
        c.argument('tags', tags_type, help='A space-delimited list of tags in "tag1[=value1]" format.')

    with self.argument_context('dms project task') as c:
        c.argument('service_name', options_list=['--service-name'])
        c.argument('project_name', options_list=['--project-name'])
        c.argument('task_name', name_arg_type, help='The name of the Task.')
        c.argument('database_options',
                   help='A JSON-formatted array of objects representing database options and table mappings.')
