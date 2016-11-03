#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from collections import OrderedDict

from azure.mgmt.resource.features.operations.features_operations import FeaturesOperations
from azure.mgmt.resource.resources.operations.resources_operations import ResourcesOperations
from azure.mgmt.resource.resources.operations.providers_operations import ProvidersOperations
from azure.mgmt.resource.resources.operations.resource_groups_operations \
    import ResourceGroupsOperations
from azure.mgmt.resource.resources.operations.tags_operations import TagsOperations
from azure.mgmt.resource.resources.operations.deployments_operations import DeploymentsOperations
from azure.mgmt.resource.resources.operations.deployment_operations_operations \
    import DeploymentOperationsOperations
from azure.mgmt.resource.policy.operations import PolicyDefinitionsOperations

from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command
from azure.cli.command_modules.resource._factory import (_resource_client_factory,
                                                         _resource_feature_client_factory,
                                                         _resource_policy_client_factory)
from azure.cli.command_modules.resource.custom import (
    list_resource_groups, create_resource_group, export_group_as_template,
    list_resources, move_resource,
    create_policy_assignment, delete_policy_assignment, show_policy_assignment, list_policy_assignment,
    create_policy_definition, update_policy_definition,
    deploy_arm_template, validate_arm_template, tag_resource, export_deployment_as_template,
    register_provider, unregister_provider,
    list_features
)

# Resource group commands
factory = lambda _: _resource_client_factory().resource_groups
cli_command('resource group delete', ResourceGroupsOperations.delete, factory)
cli_command('resource group show', ResourceGroupsOperations.get, factory)
cli_command('resource group exists', ResourceGroupsOperations.check_existence, factory)
cli_command('resource group list', list_resource_groups)
cli_command('resource group create', create_resource_group)
cli_command('resource group export', export_group_as_template)

# Resource commands
def transform_resource_list(result):
    return [OrderedDict([('Name', r['name']), ('ResourceGroup', r['resourceGroup']), \
            ('Location', r['location']), ('Type', r['type'])]) for r in result]
factory = lambda _: _resource_client_factory().resources
cli_command('resource delete', ResourcesOperations.delete, factory)
cli_command('resource show', ResourcesOperations.get, factory)
cli_command('resource list', list_resources, table_transformer=transform_resource_list)
cli_command('resource tag', tag_resource)
cli_command('resource move', move_resource)

# Resource provider commands
factory = lambda _: _resource_client_factory().providers
cli_command('provider list', ProvidersOperations.list, factory)
cli_command('provider show', ProvidersOperations.get, factory)
cli_command('provider register', register_provider)
cli_command('provider unregister', unregister_provider)

# Resource feature commands
factory = lambda _: _resource_feature_client_factory().features
cli_command('resource feature list', list_features, factory)
cli_command('resource feature show', FeaturesOperations.get, factory)
cli_command('resource feature register', FeaturesOperations.register, factory)

# Tag commands
factory = lambda _: _resource_client_factory().tags
cli_command('tag list', TagsOperations.list, factory)
cli_command('tag create', TagsOperations.create_or_update, factory)
cli_command('tag delete', TagsOperations.delete, factory)
cli_command('tag add-value', TagsOperations.create_or_update_value, factory)
cli_command('tag remove-value', TagsOperations.delete_value, factory)

# Resource group deployment commands
factory = lambda _: _resource_client_factory().deployments
cli_command('resource group deployment create', deploy_arm_template)
cli_command('resource group deployment list', DeploymentsOperations.list, factory)
cli_command('resource group deployment show', DeploymentsOperations.get, factory)
cli_command('resource group deployment delete', DeploymentsOperations.delete, factory)
cli_command('resource group deployment validate', validate_arm_template)
cli_command('resource group deployment export', export_deployment_as_template)

# Resource group deployment operations commands
factory = lambda _: _resource_client_factory().deployment_operations
cli_command('resource group deployment operation list', DeploymentOperationsOperations.list, factory)
cli_command('resource group deployment operation show', DeploymentOperationsOperations.get, factory)

cli_generic_update_command('resource update',
                           ResourcesOperations.get,
                           ResourcesOperations.create_or_update,
                           lambda: _resource_client_factory().resources)

cli_generic_update_command('resource group update',
                           ResourceGroupsOperations.get,
                           ResourceGroupsOperations.create_or_update,
                           lambda: _resource_client_factory().resource_groups)

cli_command('resource policy assignment create', create_policy_assignment)
cli_command('resource policy assignment delete', delete_policy_assignment)
cli_command('resource policy assignment list', list_policy_assignment)
cli_command('resource policy assignment show', show_policy_assignment)
factory = lambda _: _resource_policy_client_factory().policy_definitions
cli_command('resource policy definition create', create_policy_definition)
cli_command('resource policy definition delete', PolicyDefinitionsOperations.delete, factory)
cli_command('resource policy definition list', PolicyDefinitionsOperations.list, factory)
cli_command('resource policy definition show', PolicyDefinitionsOperations.get, factory)
cli_command('resource policy definition update', update_policy_definition)
