# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import register_cli_argument
from .custom import load_subscriptions


def get_subscription_id_list(prefix, **kwargs):  # pylint: disable=unused-argument
    subscriptions = load_subscriptions()
    result = []
    for subscription in subscriptions:
        result.append(subscription['id'])
        result.append(subscription['name'])
    return result


register_cli_argument('login', 'password', options_list=('--password', '-p'), help='User password or client secret. Will prompt if not given.')
register_cli_argument('login', 'service_principal', action='store_true', help='The credential representing a service principal.')
register_cli_argument('login', 'username', options_list=('--username', '-u'), help='Organization id or service principal')
register_cli_argument('login', 'tenant', options_list=('--tenant', '-t'), help='The tenant associated with the service principal.')

register_cli_argument('logout', 'username', help='account user, if missing, logout the current active account')

register_cli_argument('account', 'subscription', help='Name or ID of subscription.', completer=get_subscription_id_list)
register_cli_argument('account list', 'all_clouds', options_list=('--all',), help='List all subscriptions across all cloud environments', action='store_true')
register_cli_argument('account show', 'expanded_view', action='store_true', help="display more information like service principal's password and cloud environments")
