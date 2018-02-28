# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.commands.parameters import get_location_type

def load_arguments(self, _):

    name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')
    resource_group_name_arg_type = CLIArgumentType(options_list=('--resource-group', '-rg'), metavar='RESOURCE-GROUP')

    with self.argument_context('ams') as c:
        c.argument('media_service_name', name_arg_type, help='The name of the media service.')
        c.argument('location', arg_type=get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('resource_group_name', resource_group_name_arg_type, help='The name of the resource group within the Azure subscription.')
