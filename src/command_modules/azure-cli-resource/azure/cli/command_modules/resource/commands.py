# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from collections import OrderedDict

from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command

from azure.cli.command_modules.resource._client_factory import (_resource_client_factory,
                                                                cf_resource_groups,
                                                                cf_providers,
                                                                cf_features,
                                                                cf_tags,
                                                                cf_deployments,
                                                                cf_deployment_operations,
                                                                cf_policy_definitions)

# Resource group commands
cli_command(__name__, 'resource group delete', 'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.delete', cf_resource_groups)
cli_command(__name__, 'resource group show', 'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.get', cf_resource_groups)
cli_command(__name__, 'resource group exists', 'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.check_existence', cf_resource_groups)
cli_command(__name__, 'resource group list', 'azure.cli.command_modules.resource.custom#list_resource_groups')
cli_command(__name__, 'resource group create', 'azure.cli.command_modules.resource.custom#create_resource_group')
cli_command(__name__, 'resource group export', 'azure.cli.command_modules.resource.custom#export_group_as_template')

# Resource commands
def transform_resource_list(result):
    return [OrderedDict([('Name', r['name']), ('ResourceGroup', r['resourceGroup']), \
            ('Location', r['location']), ('Type', r['type'])]) for r in result]

cli_command(__name__, 'resource delete', 'azure.cli.command_modules.resource.custom#delete_resource')
cli_command(__name__, 'resource show', 'azure.cli.command_modules.resource.custom#show_resource')
cli_command(__name__, 'resource list', 'azure.cli.command_modules.resource.custom#list_resources', table_transformer=transform_resource_list)
cli_command(__name__, 'resource tag', 'azure.cli.command_modules.resource.custom#tag_resource')
cli_command(__name__, 'resource move', 'azure.cli.command_modules.resource.custom#move_resource')

# Resource provider commands
cli_command(__name__, 'provider list', 'azure.mgmt.resource.resources.operations.providers_operations#ProvidersOperations.list', cf_providers)
cli_command(__name__, 'provider show', 'azure.mgmt.resource.resources.operations.providers_operations#ProvidersOperations.get', cf_providers)
cli_command(__name__, 'provider register', 'azure.cli.command_modules.resource.custom#register_provider')
cli_command(__name__, 'provider unregister', 'azure.cli.command_modules.resource.custom#unregister_provider')

# Resource feature commands
cli_command(__name__, 'resource feature list', 'azure.cli.command_modules.resource.custom#list_features', cf_features)
cli_command(__name__, 'resource feature show', 'azure.mgmt.resource.features.operations.features_operations#FeaturesOperations.get', cf_features)
cli_command(__name__, 'resource feature register', 'azure.mgmt.resource.features.operations.features_operations#FeaturesOperations.register', cf_features)

# Tag commands
cli_command(__name__, 'tag list', 'azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.list', cf_tags)
cli_command(__name__, 'tag create', 'azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.create_or_update', cf_tags)
cli_command(__name__, 'tag delete', 'azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.delete', cf_tags)
cli_command(__name__, 'tag add-value', 'azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.create_or_update_value', cf_tags)
cli_command(__name__, 'tag remove-value', 'azure.mgmt.resource.resources.operations.tags_operations#TagsOperations.delete_value', cf_tags)

# Resource group deployment commands
cli_command(__name__, 'resource group deployment create', 'azure.cli.command_modules.resource.custom#deploy_arm_template')
cli_command(__name__, 'resource group deployment list', 'azure.mgmt.resource.resources.operations.deployments_operations#DeploymentsOperations.list', cf_deployments)
cli_command(__name__, 'resource group deployment show', 'azure.mgmt.resource.resources.operations.deployments_operations#DeploymentsOperations.get', cf_deployments)
cli_command(__name__, 'resource group deployment delete', 'azure.mgmt.resource.resources.operations.deployments_operations#DeploymentsOperations.delete', cf_deployments)
cli_command(__name__, 'resource group deployment validate', 'azure.cli.command_modules.resource.custom#validate_arm_template')
cli_command(__name__, 'resource group deployment export', 'azure.cli.command_modules.resource.custom#export_deployment_as_template')

# Resource group deployment operations commands
cli_command(__name__, 'resource group deployment operation list', 'azure.mgmt.resource.resources.operations.deployment_operations_operations#DeploymentOperationsOperations.list', cf_deployment_operations)
cli_command(__name__, 'resource group deployment operation show', 'azure.mgmt.resource.resources.operations.deployment_operations_operations#DeploymentOperationsOperations.get', cf_deployment_operations)

cli_generic_update_command(__name__, 'resource update',
                           'azure.mgmt.resource.resources.operations.resources_operations#ResourcesOperations.get',
                           'azure.mgmt.resource.resources.operations.resources_operations#ResourcesOperations.create_or_update',
                           lambda: _resource_client_factory().resources)

cli_generic_update_command(__name__, 'resource group update',
                           'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.get',
                           'azure.mgmt.resource.resources.operations.resource_groups_operations#ResourceGroupsOperations.create_or_update',
                           lambda: _resource_client_factory().resource_groups)

cli_command(__name__, 'resource policy assignment create', 'azure.cli.command_modules.resource.custom#create_policy_assignment')
cli_command(__name__, 'resource policy assignment delete', 'azure.cli.command_modules.resource.custom#delete_policy_assignment')
cli_command(__name__, 'resource policy assignment list', 'azure.cli.command_modules.resource.custom#list_policy_assignment')
cli_command(__name__, 'resource policy assignment show', 'azure.cli.command_modules.resource.custom#show_policy_assignment')

cli_command(__name__, 'resource policy definition create', 'azure.cli.command_modules.resource.custom#create_policy_definition')
cli_command(__name__, 'resource policy definition delete', 'azure.mgmt.resource.policy.operations#PolicyDefinitionsOperations.delete', cf_policy_definitions)
cli_command(__name__, 'resource policy definition list', 'azure.mgmt.resource.policy.operations#PolicyDefinitionsOperations.list', cf_policy_definitions)
cli_command(__name__, 'resource policy definition show', 'azure.mgmt.resource.policy.operations#PolicyDefinitionsOperations.get', cf_policy_definitions)
cli_command(__name__, 'resource policy definition update', 'azure.cli.command_modules.resource.custom#update_policy_definition')
