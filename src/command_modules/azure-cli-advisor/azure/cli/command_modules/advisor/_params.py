# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import \
    (get_enum_type,
     get_resource_name_completion_list)

from ._validators import \
    (validate_include_or_exclude,
     validate_ids_or_names,
     validate_ids_or_resource_group,
     validate_threshold_or_resource_group)


def load_arguments(self, _):
    ids_arg_type = CLIArgumentType(nargs='+', options_list=['--ids'],
                                   help='One or more resource IDs (space-delimited). If provided, no other '
                                        '"Resource Id" arguments should be specified.')

    name_arg_type = CLIArgumentType(options_list=['--name', '-n'],
                                    help='The name of the recommendation as output by the list command.',
                                    completer=get_resource_name_completion_list('Microsoft.Advisor/recommendations'))

    with self.argument_context('advisor recommendation list') as c:
        c.argument('ids', ids_arg_type, validator=validate_ids_or_resource_group)
        c.argument('category', options_list=['--category', '-c'], help='Name of recommendation category.',
                   arg_type=get_enum_type(['Cost', 'HighAvailability', 'Performance', 'Security']))
        c.argument('refresh', options_list=['--refresh', '-r'], action='store_true',
                   help='Generate new recommendations.')

    with self.argument_context('advisor recommendation disable') as c:
        c.argument('ids', ids_arg_type, arg_group="Resource Id", validator=validate_ids_or_names)
        c.argument('recommendation_name', name_arg_type, arg_group="Resource Id")
        c.argument('resource_group_name', arg_group="Resource Id")
        c.argument('days', options_list=['--days', '-d'], type=int,
                   help='Number of days to disable. If not specified, the recommendation is disabled forever.')

    with self.argument_context('advisor recommendation enable') as c:
        c.argument('ids', ids_arg_type, arg_group="Resource Id", validator=validate_ids_or_names)
        c.argument('resource_group_name', arg_group="Resource Id")
        c.argument('recommendation_name', name_arg_type, arg_group="Resource Id")

    with self.argument_context('advisor configuration update') as c:
        c.argument('low_cpu_threshold', options_list=['--low-cpu-threshold', '-l'],
                   help='Value for low CPU threshold.', arg_type=get_enum_type(['5', '10', '15', '20']),
                   validator=validate_threshold_or_resource_group)
        c.argument('exclude', options_list=['--exclude', '-e'], action='store_true',
                   help='Exclude from recommendation generation.')
        c.argument('include', options_list=['--include', '-i'], action='store_true',
                   help='Include in recommendation generation.', validator=validate_include_or_exclude)
