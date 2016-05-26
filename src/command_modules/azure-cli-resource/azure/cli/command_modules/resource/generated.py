# pylint: disable=line-too-long
from azure.mgmt.resource.resources.operations.resources_operations import ResourcesOperations
from azure.mgmt.resource.resources.operations.providers_operations import ProvidersOperations
from azure.mgmt.resource.resources.operations.resource_groups_operations \
    import ResourceGroupsOperations
from azure.mgmt.resource.resources.operations.tags_operations import TagsOperations
from azure.mgmt.resource.resources.operations.deployments_operations import DeploymentsOperations
from azure.mgmt.resource.resources.operations.deployment_operations_operations \
    import DeploymentOperationsOperations

from azure.cli.commands import CommandTable, LongRunningOperation
from azure.cli.commands.command_types import cli_command
from azure.cli.command_modules.resource._factory import _resource_client_factory
from azure.cli.command_modules.resource.custom import (
    list_resource_groups, create_resource_group, export_group_as_template, list_resources,
    deploy_arm_template, tag_resource
)

command_table = CommandTable()

# Resource group commands
factory = lambda _: _resource_client_factory().resource_groups
cli_command(command_table, 'resource group delete', ResourceGroupsOperations.delete, LongRunningOperation(), factory)
cli_command(command_table, 'resource group show', ResourceGroupsOperations.get, 'ResourceGroup', factory)
cli_command(command_table, 'resource group exists', ResourceGroupsOperations.check_existence, 'Bool', factory)
cli_command(command_table, 'resource group list', list_resource_groups, '[ResourceGroup]')
cli_command(command_table, 'resource group create', create_resource_group, 'ResourceGroup')
cli_command(command_table, 'resource group export', export_group_as_template, None)

# Resource commands
factory = lambda _: _resource_client_factory().resources
cli_command(command_table, 'resource exists', ResourcesOperations.check_existence, 'Result', factory)
cli_command(command_table, 'resource delete', ResourcesOperations.delete, 'Result', factory)
cli_command(command_table, 'resource show', ResourcesOperations.get, 'Resource', factory)
cli_command(command_table, 'resource list', list_resources, '[Resource]')
cli_command(command_table, 'resource deploy', deploy_arm_template, 'Resource')
cli_command(command_table, 'resource tag', tag_resource, 'Result')

# Resource provider commands
factory = lambda _: _resource_client_factory().providers
cli_command(command_table, 'resource provider list', ProvidersOperations.list, '[Provider]', factory)
cli_command(command_table, 'resource provider show', ProvidersOperations.get, 'Provider', factory)

# Tag commands
factory = lambda _: _resource_client_factory().tags
cli_command(command_table, 'tag list', TagsOperations.list, '[Tag]', factory)
cli_command(command_table, 'tag create', TagsOperations.create_or_update, 'Tag', factory)
cli_command(command_table, 'tag delete', TagsOperations.delete, None, factory)
cli_command(command_table, 'tag add-value', TagsOperations.create_or_update_value, 'Tag', factory)
cli_command(command_table, 'tag remove-value', TagsOperations.delete_value, None, factory)

# Resource group deployment commands
factory = lambda _: _resource_client_factory().deployments
cli_command(command_table, 'resource group deployment list', DeploymentsOperations.list, '[Deployment]', factory)
cli_command(command_table, 'resource group deployment show', DeploymentsOperations.get, 'Deployment', factory)
cli_command(command_table, 'resource group deployment validate', DeploymentsOperations.validate, 'Result', factory)
cli_command(command_table, 'resource group deployment exists', DeploymentsOperations.check_existence, 'Bool', factory)

# Resource group deployment operations commands
factory = lambda _: _resource_client_factory().deployment_operations
cli_command(command_table, 'resource group deployment operations list', DeploymentOperationsOperations.list, '[DeploymentOperation]', factory)
cli_command(command_table, 'resource group deployment operations show', DeploymentOperationsOperations.get, 'DeploymentOperation', factory)
