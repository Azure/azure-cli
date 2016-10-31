#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliArgumentType, register_cli_argument
from azure.cli.core.commands.parameters import (
    name_type,
    resource_group_name_type)

# pylint: disable=line-too-long

registry_name = CliArgumentType(
    options_list=('--registry-name', '-r'),
    help='Azure container registry name. A new Azure container registry is created if omitted or does not exist.'
)

registry_resource_id = CliArgumentType(
    options_list=('--registry-resource-id',),
    help='Azure container registry resource id. Specifies an existing Azure container registry. e.g. /subscriptions/{subscriptionId}/resourcegroups/{resourceGroup}/providers/Microsoft.ContainerRegistry/registries/{registryName}'
)

remote_url = CliArgumentType(
    options_list=('--remote-url', '-u'),
    help='Remote url of the GitHub or VSTS source repository that will be built and deployed. If omitted, a source repository will be searched for in the current working directory.'
)

remote_branch = CliArgumentType(		
    options_list=('--remote-branch', '-b'),		
    help='Remote branch of the GitHub or VSTS source repository that will be built and deployed. If omitted refs/heads/master will be selected'		
)

remote_access_token = CliArgumentType(
    options_list=('--remote-access-token', '-t'),
    help='GitHub personal access token (minimum permission is "repo"). Required if the source repository is in GitHub.'
)

vsts_account_name = CliArgumentType(
    options_list=('--vsts-account-name',),
    help='VSTS account name to create the build and release definitions. A new VSTS account is created if omitted or does not exist.'
)

vsts_project_name = CliArgumentType(
    options_list=('--vsts-project-name',),
    help='VSTS project name to create the build and release definitions. A new VSTS project is created if omitted or does not exist.'
)

register_cli_argument('vsts release create', 'name', name_type)
register_cli_argument('vsts release create', 'resource_group_name', resource_group_name_type)
register_cli_argument('vsts release create', 'registry_name', registry_name)
register_cli_argument('vsts release create', 'registry_resource_id', registry_resource_id)
register_cli_argument('vsts release create', 'remote_url', remote_url)
register_cli_argument('vsts release create', 'remote_branch', remote_branch)
register_cli_argument('vsts release create', 'remote_access_token', remote_access_token)
register_cli_argument('vsts release create', 'vsts_account_name', vsts_account_name)
register_cli_argument('vsts release create', 'vsts_project_name', vsts_project_name)

register_cli_argument('vsts build create', 'name', name_type)
register_cli_argument('vsts build create', 'resource_group_name', resource_group_name_type)
register_cli_argument('vsts build create', 'registry_name', registry_name)
register_cli_argument('vsts build create', 'registry_resource_id', registry_resource_id)
register_cli_argument('vsts build create', 'remote_url', remote_url)
register_cli_argument('vsts build create', 'remote_branch', remote_branch)
register_cli_argument('vsts build create', 'remote_access_token', remote_access_token)
register_cli_argument('vsts build create', 'vsts_account_name', vsts_account_name)
register_cli_argument('vsts build create', 'vsts_project_name', vsts_project_name)

register_cli_argument('vsts release list', 'name', name_type)
register_cli_argument('vsts release list', 'resource_group_name', resource_group_name_type)
