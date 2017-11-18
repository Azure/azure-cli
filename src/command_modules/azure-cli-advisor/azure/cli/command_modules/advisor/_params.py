# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import register_cli_argument
from azure.cli.core.commands.parameters import resource_group_name_type
from azure.cli.core.util import CLIError

def validate_include_or_exclude(namespace):
    if namespace.include and namespace.exclude:
        raise CLIError('usage error: --include | --exclude')


register_cli_argument(
    'advisor recommendation list',
    'ids',
    nargs='+',
    options_list=('--ids'),
    help='One or more resource IDs (space delimited). If provided, no other "Resource Id" arguments should be specified.'  # pylint: disable=line-too-long
)

register_cli_argument(
    'advisor recommendation list',
    'resource_group_name',
    resource_group_name_type
)

register_cli_argument(
    'advisor recommendation list',
    'category',
    options_list=('--category', '-c'),
    help='Name of recommendation category (Cost, HighAvailability, Performance or Security).'
)

register_cli_argument(
    'advisor recommendation disable',
    'ids',
    nargs='+',
    options_list=('--ids'),
    help='One or more resource IDs (space delimited). If provided, no other "Resource Id" arguments should be specified.'  # pylint: disable=line-too-long
)

register_cli_argument(
    'advisor recommendation disable',
    'days',
    options_list=('--days', '-d'),
    type=int,
    help='Number of days to disable. If not specified, the recommendation is disabled forever.'
)

register_cli_argument(
    'advisor recommendation enable',
    'ids',
    nargs='+',
    options_list=('--ids'),
    help='One or more resource IDs (space delimited). If provided, no other "Resource Id" arguments should be specified.'  # pylint: disable=line-too-long
)

register_cli_argument(
    'advisor configuration get',
    'resource_group_name',
    resource_group_name_type
)

register_cli_argument(
    'advisor configuration set',
    'resource_group_name',
    resource_group_name_type
)

register_cli_argument(
    'advisor configuration set',
    'low_cpu_threshold',
    options_list=('--low-cpu-threshold', '-l'),
    type=int,
    help='Value for low CPU threshold (5, 10, 15 or 20).'
)

register_cli_argument(
    'advisor configuration set',
    'exclude',
    options_list=('--exclude', '-e'),
    action='store_true',
    help='Exclude from recommendation generation.',
    validator=validate_include_or_exclude
)

register_cli_argument(
    'advisor configuration set',
    'include',
    options_list=('--include', '-i'),
    action='store_true',
    help='Include in recommendation generation.',
    validator=validate_include_or_exclude
)
