# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import register_cli_argument


def get_offer_type_completion_list(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
    return ['MS-AZR-0017P', 'MS-AZR-0148P']


register_cli_argument('subscriptiondefinition show', 'subscription_definition_name', options_list=('--name', '-n'), required=True, help='Name of the subscription definition to show.')
register_cli_argument('subscriptiondefinition create', 'name', options_list=('--name', '-n'), required=True, help='Name of the subscription definition.')
register_cli_argument('subscriptiondefinition create', 'offer_type', options_list=('--offer_type', '-ot'), required=True, help='The subscription\'s offer type.', completer=get_offer_type_completion_list)
register_cli_argument('subscriptiondefinition create', 'subscription_display_name', options_list=('--subscription_display_name', '-sdn'), required=False, help='The subscription display name of the subscription definition.')
