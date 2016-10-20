#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
import json

from azure.cli.core.commands import register_cli_argument

from azure.cli.core.cloud import get_clouds, get_custom_clouds

# pylint: disable=line-too-long

def get_cloud_name_completion_list(prefix, action, parsed_args, **kwargs):#pylint: disable=unused-argument
    return [c.name for c in get_clouds()]

def get_custom_cloud_name_completion_list(prefix, action, parsed_args, **kwargs):#pylint: disable=unused-argument
    return [c.name for c in get_custom_clouds()]

register_cli_argument('cloud', 'cloud_name', options_list=('--name', '-n'),
                      help='Name of the registered cloud',
                      completer=get_cloud_name_completion_list)

register_cli_argument('cloud register', 'cloud_config', options_list=('--cloud-config',),
                      help='JSON encoded cloud configuration. Use @{file} to load from a file.',
                      type=json.loads)

register_cli_argument('cloud unregister', 'cloud_name',
                      completer=get_custom_cloud_name_completion_list)
