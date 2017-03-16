# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliArgumentType, register_cli_argument
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

dns_prefix = CliArgumentType(
    options_list=('--dns-prefix', '-d'),
    help='Prefix used to create a unique fully qualified domain name (FQDN) for the master.'
)

location = CliArgumentType(
    options_list=('--location', '-l'),
    help='Azure region for the Azure Container Service deployment.',
    default='westus',
    required=False
)

user_name = CliArgumentType(
    options_list=('--admin-username', '-u'),
    help='User name for an account on each of the Linux virtual machines in the cluster.',
    default='azureuser',
    required=False
)

name_arg_type = CliArgumentType(
    options_list=('--name', '-n'),
    metavar='NAME')

register_cli_argument('project', 'remote_access_token', remote_access_token)
register_cli_argument('project', 'project_path', project_path)
register_cli_argument('project', 'dns_prefix', dns_prefix)
register_cli_argument('project', 'location', location)
register_cli_argument('project', 'user_name', user_name)


register_cli_argument('project', 'name', name_arg_type)
register_cli_argument('project', 'resource_group', resource_group_name_type)
register_cli_argument('project', 'location', location_type)
