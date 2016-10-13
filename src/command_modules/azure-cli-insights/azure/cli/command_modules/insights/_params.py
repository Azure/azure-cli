#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import json

from azure.cli.core.commands import register_cli_argument
from azure.cli.core.commands.parameters import ignore_type

# ARGUMENT ALIASING

register_cli_argument('insights', 'api_version', ignore_type)
register_cli_argument('insights', 'limit', type=int)

register_cli_argument('insights event', 'select', nargs='+')

register_cli_argument('insights alerts rule create', 'parameters', options_list=('--alert-rule-resource',), help='JSON encoded alert rule resource. Use @{file} to load from a file.', type=json.loads)

for item in ['correlation_id', 'resource_id', 'resource_provider']:
    register_cli_argument('insights event list', item, arg_group='Top-Level Filter')
register_cli_argument('insights event list', 'resource_group_name', help='Filter by resource group.', arg_group='Top-Level Filter')
