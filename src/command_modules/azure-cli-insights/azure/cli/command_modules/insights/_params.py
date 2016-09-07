#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.commands import register_cli_argument
from azure.cli.commands.parameters import ignore_type

# ARGUMENT ALIASING

register_cli_argument('insights', 'api_version', ignore_type)
register_cli_argument('insights', 'limit', type=int)

register_cli_argument('insights event', 'select', nargs='+')

for item in ['correlation_id', 'resource_id', 'resource_provider']:
    register_cli_argument('insights event list', item, arg_group='Top-Level Filter')
register_cli_argument('insights event list', 'resource_group_name', help='Filter by resource group.', arg_group='Top-Level Filter')
