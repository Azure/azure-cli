# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.commands.parameters import (get_location_type, get_three_state_flag)

from azure.cli.command_modules.role._completers import get_role_definition_name_completion_list

def load_arguments(self, _):

    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')
    storage_account_arg_type = CLIArgumentType(options_list=('--storage-account'), metavar='STORAGE_NAME')

    with self.argument_context('ams') as c:
        c.argument('account_name', name_arg_type, help='The name of the Azure Media Services account within the resource group.')
        c.argument('location', arg_type=get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)

    with self.argument_context('ams create') as c:
        c.argument('storage_account', storage_account_arg_type, help='The name of the primary storage account to attach to the Azure Media Services account.')

    with self.argument_context('ams storage add') as c:
        c.argument('storage_account', storage_account_arg_type, help='The name of the secondary storage account to attach to the Azure Media Services account.')

    with self.argument_context('ams storage remove') as c:
        c.argument('storage_account', storage_account_arg_type, help='The name of the secondary storage account to detach from the Azure Media Services account.')

    with self.argument_context('ams sp create') as c:
        c.argument('sp_name', help='The name or app URI to associate the RBAC with. If not present, a name will be generated.')
        c.argument('sp_password', help='The password used to log in. If not present, a random password will be generated.')
        c.argument('role', completer=get_role_definition_name_completion_list)
        c.argument('xml', help='Enables xml output format.')
