#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliArgumentType, register_cli_argument
from azure.cli.core.commands.parameters import (
    name_type,
    resource_group_name_type, 
    get_resource_group_completion_list)

registry_name = CliArgumentType(
    options_list=('--registry-name', '-r'),
    help='Docker registry name', 
    required = False
)

registry_resource_group = CliArgumentType(
    options_list=('--registry-resource-group',),
    help='Docker registry resource group name',
    required = False
)

remote_url = CliArgumentType(
    options_list=('--remote-url', '-u'),
    help='Remote url (The remote url of the repository to deploy.)',
    required = False
)

remote_access_token = CliArgumentType(
    options_list=('--remote-access-token', '-t'),
    help='Remote access token (GitHub needs repo, user, admin:repo_hook permissions)',
    required = False
)

vsts_account_name = CliArgumentType(
    options_list=('--vsts-account-name',),
    help='VSTS account name',
    required = False
)

vsts_project_name = CliArgumentType(
    options_list=('--vsts-project-name',),
    help='VSTS project name',
    required= False
)

register_cli_argument('devops release create', 'name', arg_type=name_type)
register_cli_argument('devops release create', 'resource_group_name', arg_type=resource_group_name_type, completer=get_resource_group_completion_list)
register_cli_argument('devops release create', 'registry_name', registry_name)
register_cli_argument('devops release create', 'registry_resource_group', registry_resource_group)
register_cli_argument('devops release create', 'remote_url', remote_url)
register_cli_argument('devops release create', 'remote_access_token', remote_access_token)
register_cli_argument('devops release create', 'vsts_account_name', vsts_account_name)
register_cli_argument('devops release create', 'vsts_project_name', vsts_project_name)

register_cli_argument('devops build create', 'name', arg_type=name_type)
register_cli_argument('devops build create', 'resource_group_name', arg_type=resource_group_name_type, completer=get_resource_group_completion_list)
register_cli_argument('devops build create', 'registry_name', registry_name)
register_cli_argument('devops build create', 'registry_resource_group', registry_resource_group)
register_cli_argument('devops build create', 'remote_url', remote_url)
register_cli_argument('devops build create', 'remote_access_token', remote_access_token)
register_cli_argument('devops build create', 'vsts_account_name', vsts_account_name)
register_cli_argument('devops build create', 'vsts_project_name', vsts_project_name)

register_cli_argument('devops release list', 'name', arg_type=name_type)
register_cli_argument('devops release list', 'resource_group_name', arg_type=resource_group_name_type, completer=get_resource_group_completion_list)