# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse
from azure.cli.core.commands import register_cli_argument
from .custom import load_subscriptions


def get_subscription_id_list(prefix, **kwargs):  # pylint: disable=unused-argument
    subscriptions = load_subscriptions()
    result = []
    for subscription in subscriptions:
        result.append(subscription['id'])
        result.append(subscription['name'])
    return result


register_cli_argument('login', 'password', options_list=('--password', '-p'), help="Credentials like user password, or for a service principal, provide client secret or a pem file with key and public certificate. Will prompt if not given.")
register_cli_argument('login', 'service_principal', action='store_true', help='The credential representing a service principal.')
register_cli_argument('login', 'username', options_list=('--username', '-u'), help='Organization id or service principal')
register_cli_argument('login', 'tenant', options_list=('--tenant', '-t'), help='The AAD tenant, must provide when using service principals.')
register_cli_argument('login', 'allow_no_subscriptions', action='store_true', help="Support access tenants without subscriptions. It's uncommon but useful to run tenant level commands, such as 'az ad'")

register_cli_argument('logout', 'username', help='account user, if missing, logout the current active account')

register_cli_argument('account', 'subscription', options_list=('--subscription', '-s'), help='Name or ID of subscription.', completer=get_subscription_id_list)
register_cli_argument('account list', 'all', help="List all subscriptions, rather just 'Enabled' ones", action='store_true')
register_cli_argument('account show', 'expanded_view', action='store_true', help=argparse.SUPPRESS)  # supress because this is being deprecated
