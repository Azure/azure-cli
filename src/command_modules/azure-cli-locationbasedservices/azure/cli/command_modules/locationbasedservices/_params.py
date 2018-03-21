# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (
    get_enum_type,
    get_resource_name_completion_list,
    resource_group_name_type,
    tags_type)

from azure.cli.command_modules.locationbasedservices.validators import validate_account_name
from azure.mgmt.locationbasedservices.models.location_based_services_management_client_enums import KeyType


def load_arguments(self, _):
    # Argument Definition
    locationbasedservices_name_type = CLIArgumentType(options_list=['--name', '-n'],
                                                      completer=get_resource_name_completion_list(
                                                          'Microsoft.LocationBasedServices/accounts'),
                                                      help='The name of the Location Based Services Account',
                                                      validator=validate_account_name)

    # Parameter Registration
    with self.argument_context('locationbasedservices') as c:
        c.argument('resource_group_name',
                   arg_type=resource_group_name_type,
                   id_part='resource_group',
                   help='Resource group name')
        c.argument('account_name',
                   id_part='name',
                   arg_type=locationbasedservices_name_type)

    with self.argument_context('locationbasedservices account') as c:
        c.argument('sku_name',
                   options_list=['--sku', '-s'],
                   help='The name of the SKU, in standard format (such as S0).',
                   arg_type=get_enum_type(['S0']),
                   required=False)
        c.argument('tags',
                   arg_type=tags_type)

    with self.argument_context('locationbasedservices account create') as c:
        c.argument('agree',
                   options_list=['--agree-to-the-preview-terms'],
                   help='You agree to the Preview Terms. Ignore prompt for confirmation.',
                   action='store_true')

    with self.argument_context('locationbasedservices account update') as c:
        c.ignore('agree')

    # Prevent --ids argument in keys with id_part=None
    with self.argument_context('locationbasedservices account keys') as c:
        c.argument('account_name',
                   id_part=None,
                   arg_type=locationbasedservices_name_type)

    with self.argument_context('locationbasedservices account keys renew') as c:
        c.argument('key_type',
                   options_list=['--key'],
                   arg_type=get_enum_type(KeyType))
