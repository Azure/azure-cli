# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.parameters import get_enum_type


# pylint: disable=line-too-long
def load_arguments(self, _):
    with self.argument_context('account subscriptiondefinition create') as c:
        c.argument('offer_type', required=True, help='The subscription\'s offer type.', arg_type=get_enum_type(['MS-AZR-0017P', 'MS-AZR-0148P']))
        c.argument('subscription_display_name', options_list=['--subscription-display-name', '-sdn'], help='The subscription display name of the subscription definition.')

    for scope in ['account subscriptiondefinition create', 'account subscriptiondefinition show']:
        with self.argument_context(scope) as c:
            c.argument('subscription_definition_name', options_list=['--name', '-n'], help='Name of the subscription definition.')
