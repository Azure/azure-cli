# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import (
    get_enum_type, 
    get_three_state_flag,
    resource_group_name_type,
)


def load_arguments(self, _):
    project_name_type = CLIArgumentType(
        options_list=['--project-name'],
        help='Name of the Azure Migrate project.',
        id_part='name'
    )
    
    subscription_id_type = CLIArgumentType(
        options_list=['--subscription-id'],
        help='Azure subscription ID. Uses the default subscription if not specified.'
    )

    with self.argument_context('migrate') as c:
        c.argument('subscription_id', subscription_id_type)

    with self.argument_context('migrate local get-protected-item') as c:
        c.argument('protected_item_id', help='Full ARM resource ID of the protected item to retrieve.', required=True)

    with self.argument_context('migrate local get-discovered-server') as c:
        c.argument('project_name', project_name_type, required=True)
        c.argument('resource_group_name', 
                   options_list=['--resource-group-name', '--resource-group', '-g'], 
                   help='Name of the resource group containing the Azure Migrate project.', 
                   required=True)
        c.argument('display_name', help='Display name of the source machine to filter by.')
        c.argument('source_machine_type', arg_type=get_enum_type(['VMware', 'HyperV']), help='Type of the source machine.')
        c.argument('subscription_id', subscription_id_type)
        c.argument('name', help='Internal name of the specific source machine to retrieve.')
        c.argument('appliance_name', help='Name of the appliance (site) containing the machines.')