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
