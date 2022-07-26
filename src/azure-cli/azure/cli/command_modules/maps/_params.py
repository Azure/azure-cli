# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (
    get_enum_type,
    get_resource_name_completion_list,
    resource_group_name_type,
    tags_type,
    get_location_type,
    get_three_state_flag)
from azure.cli.core.commands.validators import (
    get_default_location_from_resource_group,
    validate_file_or_dict
)

from azure.mgmt.maps.models import KeyType
from azure.cli.command_modules.maps.action import AddLinkedResources


def load_arguments(self, _):
    # Argument Definition
    maps_name_type = CLIArgumentType(options_list=['--name', '--account-name', '-n'],
                                     completer=get_resource_name_completion_list('Microsoft.Maps/accounts'),
                                     help='The name of the maps account')

    # Parameter Registration
    with self.argument_context('maps') as c:
        c.argument('resource_group_name',
                   arg_type=resource_group_name_type,
                   id_part='resource_group',
                   help='Resource group name')
        c.argument('account_name',
                   id_part='name',
                   arg_type=maps_name_type)

    with self.argument_context('maps account') as c:
        c.argument('name', options_list=['--sku', '-s'], arg_type=get_enum_type(['S0', 'S1', 'G2']),
                   help='The name of the SKU, in standard format (such as S0).', arg_group='Sku',
                   required=True)
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('maps account create') as c:
        c.argument('kind', options_list=['--kind'], arg_type=get_enum_type(['Gen1', 'Gen2']),
                   help='Get or Set Kind property.')
        c.argument('disable_local_auth', options_list=['--disable-local-auth'], arg_type=get_three_state_flag(),
                   help='Allows toggle functionality on Azure '
                   'Policy to disable Azure Maps local authentication support. This will disable Shared Keys '
                   'authentication from any usage.')
        c.argument('linked_resources', options_list=['--linked-resources'], action=AddLinkedResources, nargs='+',
                   help='Sets the resources to be used for '
                   'Managed Identities based operations for the Map account resource.')
        c.argument('type_', options_list=['--type'], arg_type=get_enum_type(['SystemAssigned', 'UserAssigned',
                                                                             'SystemAssigned, UserAssigned', 'None']),
                   help='The identity type.', arg_group='Identity')
        c.argument('user_assigned_identities', options_list=['--user-identities'], type=validate_file_or_dict,
                   help='The list of user identities associated with the resource. '
                   'The user identity dictionary key references will be ARM resource ids '
                   'in the form: \'/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microso'
                   'ft.ManagedIdentity/userAssignedIdentities/{identityName}\'. Expected value: '
                   'json-string/@json-file.', arg_group='Identity')
        c.argument('force', options_list=['--accept-tos'], action='store_true',
                   help='You must agree to the License and Privacy Statement to create an account.')

    with self.argument_context('maps account update') as c:
        c.argument('kind', options_list=['--kind'], arg_type=get_enum_type(['Gen1', 'Gen2']),
                   help='Get or Set Kind property.')
        c.argument('disable_local_auth', options_list=['--disable-local-auth'], arg_type=get_three_state_flag(),
                   help='Allows toggle functionality on Azure '
                   'Policy to disable Azure Maps local authentication support. This will disable Shared Keys '
                   'authentication from any usage.')
        c.argument('linked_resources', options_list=['--linked-resources'], action=AddLinkedResources, nargs='+',
                   help='Sets the resources to be used for '
                   'Managed Identities based operations for the Map account resource.')
        c.argument('type_', options_list=['--type'], arg_type=get_enum_type(['SystemAssigned', 'UserAssigned',
                                                                             'SystemAssigned, UserAssigned', 'None']),
                   help='The identity type.', arg_group='Identity')
        c.argument('user_assigned_identities', options_list=['--user-identities'], type=validate_file_or_dict,
                   help='The list of user identities associated with the resource. '
                   'The user identity dictionary key references will be ARM resource ids '
                   'in the form: \'/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microso'
                   'ft.ManagedIdentity/userAssignedIdentities/{identityName}\'. Expected value: '
                   'json-string/@json-file.', arg_group='Identity')

    # Prevent --ids argument in keys with id_part=None
    with self.argument_context('maps account keys') as c:
        c.argument('account_name',
                   id_part=None,
                   arg_type=maps_name_type)

    with self.argument_context('maps account keys renew') as c:
        c.argument('key_type',
                   options_list=['--key'],
                   arg_type=get_enum_type(KeyType),
                   help='Whether the operation refers to the primary or secondary key')

    with self.argument_context('maps creator') as c:
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('maps creator create') as c:
        c.argument('creator_name', options_list=['--creator-name'], type=str, help='The name of the '
                   'Maps Creator instance.')
        c.argument('location', options_list=['--location', '-l'], arg_type=get_location_type(self.cli_ctx),
                   required=False, validator=get_default_location_from_resource_group)
        c.argument('storage_units', options_list=['--storage-units'], type=int,
                   help='The storage units to be allocated. Integer values from 1 to 100, inclusive.')

    with self.argument_context('maps creator update') as c:
        c.argument('creator_name', options_list=['--creator-name'], type=str, help='The name of the '
                   'Maps Creator instance.', id_part='child_name_1')
        c.argument('storage_units', options_list=['--storage-units'], type=int,
                   help='The storage units to be allocated. Integer values from 1 to 100, inclusive.')

    with self.argument_context('maps creator delete') as c:
        c.argument('creator_name', options_list=['--creator-name'], type=str, help='The name of the '
                   'Maps Creator instance.', id_part='child_name_1')

    with self.argument_context('maps creator show') as c:
        c.argument('creator_name', options_list=['--creator-name'], type=str, help='The name of the '
                   'Maps Creator instance.', id_part='child_name_1')

    with self.argument_context('maps creator list') as c:
        c.argument('resource_group_name',
                   arg_type=resource_group_name_type,
                   id_part=None,
                   help='Resource group name')
        c.argument('account_name',
                   id_part=None,
                   arg_type=maps_name_type)
