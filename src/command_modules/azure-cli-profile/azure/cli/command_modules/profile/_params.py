# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.util import CLIError
from azure.cli.core.commands import register_cli_argument
from azure.mgmt.resource.locks.models import LockLevel
from azure.cli.core.commands.parameters import enum_choice_list
from azure.cli.core.commands.parameters import ignore_type
from azure.cli.command_modules.resource.custom import _parse_lock_id
from .custom import load_subscriptions


def get_subscription_id_list(prefix, **kwargs):  # pylint: disable=unused-argument
    subscriptions = load_subscriptions()
    result = []
    for subscription in subscriptions:
        result.append(subscription['id'])
        result.append(subscription['name'])
    return result


def validate_subscription_lock(namespace):
    if getattr(namespace, 'ids', None):
        for lock_id in getattr(namespace, 'ids'):
            if not _parse_lock_id(lock_id).get('resource_group_name'):
                raise CLIError('{} is not a valid subscription-level lock id.'.format(lock_id))


register_cli_argument('login', 'password', options_list=('--password', '-p'), help="Credentials like user password, or for a service principal, provide client secret or a pem file with key and public certificate. Will prompt if not given.")
register_cli_argument('login', 'service_principal', action='store_true', help='The credential representing a service principal.')
register_cli_argument('login', 'username', options_list=('--username', '-u'), help='Organization id or service principal')
register_cli_argument('login', 'tenant', options_list=('--tenant', '-t'), help='The AAD tenant, must provide when using service principals.')
register_cli_argument('login', 'allow_no_subscriptions', action='store_true', help="Support access tenants without subscriptions. It's uncommon but useful to run tenant level commands, such as 'az ad'")
register_cli_argument('login', 'msi', action='store_true', help="Log in using the Virtual Machine's identity", arg_group='Managed Service Identity')
register_cli_argument('login', 'msi_port', help="the port to retrieve tokens for login", arg_group='Managed Service Identity')

register_cli_argument('logout', 'username', help='account user, if missing, logout the current active account')

register_cli_argument('account', 'subscription', options_list=('--subscription', '-s'), help='Name or ID of subscription.', completer=get_subscription_id_list)
register_cli_argument('account list', 'all', help="List all subscriptions, rather just 'Enabled' ones", action='store_true')
register_cli_argument('account list', 'refresh', help="retrieve up to date subscriptions from server", action='store_true')
register_cli_argument('account show', 'show_auth_for_sdk', options_list=('--sdk-auth',), action='store_true', help='output result in compatible with Azure SDK auth file')
register_cli_argument('account lock', 'resource_group', ignore_type)
register_cli_argument('account lock', 'resource_provider_namespace', ignore_type)
register_cli_argument('account lock', 'parent_resource_path', ignore_type)
register_cli_argument('account lock', 'resource_type', ignore_type)
register_cli_argument('account lock', 'resource_name', ignore_type)
register_cli_argument('account lock', 'lock_name', options_list=('--name', '-n'), help='Name of the lock', id_part='resource_name', validator=validate_subscription_lock)
register_cli_argument('account lock', 'level', options_list=('--lock-type', '-t'), **enum_choice_list([LockLevel.can_not_delete, LockLevel.read_only]))
register_cli_argument('account lock', 'ids', nargs='+', options_list=('--ids'), help='One or more resource IDs (space delimited). If provided, no other "Resource Id" arguments should be specified.')
