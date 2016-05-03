from azure.mgmt.resource.resources.operations.resource_groups_operations \
    import ResourceGroupsOperations
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
