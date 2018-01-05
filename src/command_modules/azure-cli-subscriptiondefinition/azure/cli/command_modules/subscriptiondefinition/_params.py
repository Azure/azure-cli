# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import register_cli_argument

def get_offer_type_completion_list(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
    return ['MS-AZR-0017P', 'MS-AZR-0148P']

register_cli_argument('subscriptiondefinition list', 'management_group_id', options_list=('--management_group_id', '-mgid'), required=True, help='Management group in which to retrieve subscription definitions.')
register_cli_argument('subscriptiondefinition show', 'subscription_id', options_list=('--subscription_id', '-sid'), required=True, help='Subscription for which to retrieve the subscription definition.')
register_cli_argument('subscriptiondefinition show', 'management_group_id', options_list=('--management_group_id', '-mgid'), required=True, help='Management group in which to retrieve a subscription definition.')
register_cli_argument('subscriptiondefinition show', 'name', options_list=('--name', '-n'), required=True, help='Name of the subscription definition to retrieve.')
register_cli_argument('subscriptiondefinition create', 'management_group_id', options_list=('--management_group_id', '-mgid'), required=True, help='Management group in which to create a subscription definition.')
register_cli_argument('subscriptiondefinition create', 'name', options_list=('--name', '-n'), required=True, help='Name of the subscription definition.')
register_cli_argument('subscriptiondefinition create', 'offer_type', options_list=('--offer_type', '-ot'), required=True, help='The subscription\'s offer type.', completer=get_offer_type_completion_list)
register_cli_argument('subscriptiondefinition create', 'subscription_display_name', options_list=('--subscription_display_name', '-sdn'), required=False, help='The display name of the subscription created by the subscription definition.')
