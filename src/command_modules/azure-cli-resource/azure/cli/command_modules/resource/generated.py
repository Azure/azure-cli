from azure.mgmt.resource.resources.operations.resource_groups_operations \
    import ResourceGroupsOperations
from azure.mgmt.resource.resources.operations.tags_operations import TagsOperations
from azure.mgmt.resource.resources.operations.deployments_operations import DeploymentsOperations
from azure.mgmt.resource.resources.operations.deployment_operations_operations \
    import DeploymentOperationsOperations
from azure.cli.commands._auto_command import build_operation, AutoCommandDefinition
from azure.cli.commands import CommandTable, LongRunningOperation
from azure.cli._locale import L

from ._params import PARAMETER_ALIASES
from .custom import (_resource_client_factory,
                     ConvenienceResourceGroupCommands, ConvenienceResourceCommands)

command_table = CommandTable()

def _patch_aliases(alias_items):
    aliases = PARAMETER_ALIASES.copy()
    aliases.update(alias_items)
    return aliases

build_operation(
    'resource group', 'resource_groups', _resource_client_factory,
    [
        AutoCommandDefinition(
            ResourceGroupsOperations.delete,
            LongRunningOperation(L('Deleting resource group'), L('Resource group deleted'))),
        AutoCommandDefinition(ResourceGroupsOperations.get, 'ResourceGroup', 'show'),
        AutoCommandDefinition(ResourceGroupsOperations.check_existence, 'Bool', 'exists'),
    ],
    command_table,
    _patch_aliases({
        'resource_group_name': {'name': '--name -n'}
    }))

build_operation(
    'resource group', None, ConvenienceResourceGroupCommands,
    [
        AutoCommandDefinition(ConvenienceResourceGroupCommands.list, '[ResourceGroup]'),
        AutoCommandDefinition(ConvenienceResourceGroupCommands.create, 'ResourceGroup'),
    ],
    command_table,
    _patch_aliases({
        'resource_group_name': {'name': '--name -n'}
    }))

build_operation(
    'resource', None, ConvenienceResourceCommands,
    [
        AutoCommandDefinition(ConvenienceResourceCommands.list, '[Resource]'),
        AutoCommandDefinition(ConvenienceResourceCommands.show, 'Resource'),
    ],
    command_table,
    _patch_aliases({
        'resource_name': {'name': '--name -n'}
    }))

build_operation(
    'tag', 'tags', _resource_client_factory,
    [
        AutoCommandDefinition(TagsOperations.list, '[Tag]'),
        AutoCommandDefinition(TagsOperations.create_or_update, 'Object', 'create'),
        AutoCommandDefinition(TagsOperations.delete, None, 'delete'),
        AutoCommandDefinition(TagsOperations.create_or_update_value, 'Object', 'add-value'),
        AutoCommandDefinition(TagsOperations.delete_value, 'Object', 'remove-value'),
    ],
    command_table,
    _patch_aliases({
        'tag_name': {'name': '--name -n'},
        'tag_value': {'name': '--value'}
    }))
