# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliArgumentType, register_cli_argument

# pylint: disable=line-too-long

target_name = CliArgumentType(
    options_list=('--target-name',),
    help='Name of the Azure Container Service cluster to deploy containers to.'
)

target_resource_group = CliArgumentType(
    options_list=('--target-resource-group',),
    help='Name of the Azure Container Service cluster\'s resource group.'
)

registry_name = CliArgumentType(
    options_list=('--registry-name', '-r'),
    help='Azure Container Registry name to which container images will be pushed after each build, and pulled from to deploy container instances. If you have an existing registry at myregistry-{accountname}.azureacr.io, then set this parameter value to myregistry. A new Azure Container Registry is created if this parameter value is omitted or does not exist.'
)

registry_resource_id = CliArgumentType(
    options_list=('--registry-resource-id',),
    help='Azure container registry resource id. Specifies an existing Azure container registry. e.g. /subscriptions/{subscriptionId}/resourcegroups/{resourceGroup}/providers/Microsoft.ContainerRegistry/registries/{registryName}'
)

remote_url = CliArgumentType(
    options_list=('--remote-url', '-u'),
    help='Remote url of the GitHub or VSTS source repository that will be built and deployed. Example: https://github.com/myaccount/myrepository.git. If omitted, a source repository will be searched for in the current working directory.'
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
    help='VSTS account name to create the build and release definitions. If you have an existing VSTS account at myvstsaccount.visualstudio.com, then set this parameter value to myvstsaccount. A new VSTS account is created if parameter value is omitted or does not exist.'
)

vsts_project_name = CliArgumentType(
    options_list=('--vsts-project-name',),
    help='VSTS project name to create the build and release definitions. A new VSTS project is created if omitted or does not exist.'
)

register_cli_argument('container', 'target_name', target_name)
register_cli_argument('container', 'target_resource_group', target_resource_group)
register_cli_argument('container', 'registry_name', registry_name)
register_cli_argument('container', 'registry_resource_id', registry_resource_id)
register_cli_argument('container', 'remote_url', remote_url)
register_cli_argument('container', 'remote_branch', remote_branch)
register_cli_argument('container', 'remote_access_token', remote_access_token)
register_cli_argument('container', 'vsts_account_name', vsts_account_name)
register_cli_argument('container', 'vsts_project_name', vsts_project_name)
