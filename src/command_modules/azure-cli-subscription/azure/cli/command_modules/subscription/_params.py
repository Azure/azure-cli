# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.subscription._completers import get_offer_type_completion_list


# pylint: disable=line-too-long
def load_arguments(self, _):
    with self.argument_context('subscriptiondefinition show') as c:
        c.argument('subscription_definition_name', options_list=['--name', '-n'], required=False, help='Name of the subscription definition to show.')

    with self.argument_context('subscriptiondefinition create') as c:
        c.argument('name', options_list=['--name', '-n'], required=True, help='Name of the subscription definition.')
        c.argument('offer_type', options_list=['--offer_type', '-ot'], required=True, help='The subscription\'s offer type.', completer=get_offer_type_completion_list)
        c.argument('subscription_display_name', options_list=['--subscription_display_name', '-sdn'], required=False, help='The subscription display name of the subscription definition.')
