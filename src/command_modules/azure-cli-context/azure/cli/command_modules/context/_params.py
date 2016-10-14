#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import register_cli_argument

from azure.cli.core.cloud import get_clouds
from azure.cli.core.context import get_contexts

# pylint: disable=line-too-long

def get_cloud_name_completion_list(prefix, action, parsed_args, **kwargs):#pylint: disable=unused-argument
    return [c.name for c in get_clouds()]

def get_context_completion_list(prefix, action, parsed_args, **kwargs):#pylint: disable=unused-argument
    return [c['name'] for c in get_contexts()]

register_cli_argument('context', 'context_name', options_list=('--name', '-n'), help='Name of context', completer=get_context_completion_list)
register_cli_argument('context', 'cloud_name', options_list=('--cloud',), help='Name of the registered cloud', completer=get_cloud_name_completion_list)

register_cli_argument('context modify', 'context_name', help='Name of the context to modify. If not specified, we use the current context')
register_cli_argument('context modify', 'default_subscription', help='Name or id of the default subscription to be used with this context')
register_cli_argument('context show', 'context_name', help='Name of the context to modify. If not specified, we use the current context')

register_cli_argument('context create', 'use_later', action='store_true', help='After creating the context, do not set it to be active immediately.')
register_cli_argument('context create', 'context_name', completer=None)
