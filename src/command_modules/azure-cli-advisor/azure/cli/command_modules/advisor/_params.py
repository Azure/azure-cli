# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import register_cli_argument

register_cli_argument('advisor recommendation generate', 'timeout', options_list=('--timeout', '-t'), required=False, help='Timeout in seconds')

register_cli_argument('advisor recommendation list', 'ids', nargs='+', options_list=('--ids'), required=False, help='One or more resource IDs (space delimited). If provided, no other "Resource Id" arguments should be specified.')
register_cli_argument('advisor recommendation list', 'rg_name', options_list=('--resource-group', '-g'), required=False, help='Name of resource group.')
register_cli_argument('advisor recommendation list', 'category', options_list=('--category', '-c'), required=False, help='Name of category.')

register_cli_argument('advisor recommendation disable', 'ids', nargs='+', options_list=('--ids'), required=True, help='One or more resource IDs (space delimited). If provided, no other "Resource Id" arguments should be specified.')
register_cli_argument('advisor recommendation disable', 'name', options_list=('--name', '-n'), required=True, help='Name of the recommendation to disable.')
register_cli_argument('advisor recommendation disable', 'duration', options_list=('--duration', '-d'), required=False, help='Duration to disable.')

register_cli_argument('advisor recommendation enable', 'ids', nargs='+', options_list=('--ids'), required=True, help='One or more resource IDs (space delimited). If provided, no other "Resource Id" arguments should be specified.')
register_cli_argument('advisor recommendation enable', 'name', options_list=('--name', '-n'), required=True, help='Name of the recommendation to enable.')

register_cli_argument('advisor configuration get', 'rg_name', options_list=('--resource-group', '-g'), required=False, help='Name of resource group.')

register_cli_argument('advisor configuration set', 'rg_name', options_list=('--resource-group', '-g'), required=False, help='Name of resource group.')
register_cli_argument('advisor configuration set', 'low_cpu_threshold', options_list=('--low-cpu-threshold', '-l'), required=False, help='Value for low CPU threshold.')
register_cli_argument('advisor configuration set', 'exclude', options_list=('--exclude', '-e'), required=False, help='Whether to exclude from recommendation generation.')
