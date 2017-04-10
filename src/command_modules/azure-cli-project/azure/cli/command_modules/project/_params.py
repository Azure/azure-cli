# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from azure.cli.core.commands import (CliArgumentType, register_cli_argument)
from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    location_type)

# pylint: disable=line-too-long,invalid-name

remote_access_token = CliArgumentType(
    options_list=('--remote-access-token', '-t'),
    help='GitHub personal access token.'
)

project_path = CliArgumentType(
    options_list=('--project-path', '-p'),
    help='Project/Services path to deploy on the Kubernetes cluster or defaults to current directory.',
    default='.',
    required=False
)

ssh_private_key = CliArgumentType(
    options_list=('--ssh-private-key', '-k'),
    help='Path to SSH private key.',
    default=os.path.join(
        os.path.expanduser("~"), '.ssh', 'id_rsa'),
    required=False
)

force_create = CliArgumentType(
    options_list=('-f',),
    help='Force Project Create',
    required=False
)

wait = CliArgumentType(
    options_list=('--wait', '-w'),
    help='Wait for the long running delete resource group operation to finish.',
    required=False
)

name_arg_type = CliArgumentType(
    options_list=('--name', '-n'),
    metavar='NAME')

reference_name = CliArgumentType(
    options_list=('--reference-name', '-r'))

environment_variables = CliArgumentType(
    options_list=('--env-variables', '-e'),
    help="Space separated 'name=value' pairs",
    required=False)

optional_target_group = CliArgumentType(
    options_list=('--target-group', '-g'),
    help="Target resoure group name",
    required=False
)

optional_target_name = CliArgumentType(
    options_list=('--target-name', '-n'),
    required=False
)

register_cli_argument('project', 'remote_access_token', remote_access_token)
register_cli_argument('project', 'project_path', project_path)
register_cli_argument('project', 'ssh_private_key', ssh_private_key)
# TODO: Ideally, this should be project-name
register_cli_argument('project', 'name', name_arg_type)
register_cli_argument('project', 'resource_group', resource_group_name_type)
register_cli_argument('project', 'location', location_type)
register_cli_argument('project', 'force_create',
                      force_create, action='store_true')
register_cli_argument('project', 'wait', wait, action='store_true')
register_cli_argument('project', 'env_variables',
                      environment_variables, nargs='+')

register_cli_argument('project', 'target_group',
                      optional_target_group)
register_cli_argument('project', 'target_name', optional_target_name)
register_cli_argument('project', 'reference-name', reference_name)
