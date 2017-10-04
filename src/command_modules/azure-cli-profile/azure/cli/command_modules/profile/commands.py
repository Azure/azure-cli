# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from collections import OrderedDict

from azure.cli.core.commands import cli_command

cli_command(__name__, 'login', 'azure.cli.command_modules.profile.custom#login')
cli_command(__name__, 'logout', 'azure.cli.command_modules.profile.custom#logout')


def transform_account_list(result):
    transformed = []
    for r in result:
        res = OrderedDict([('Name', r['name']),
                           ('CloudName', r['cloudName']),
                           ('SubscriptionId', r['id']),
                           ('State', r['state']),
                           ('IsDefault', r['isDefault'])])
        transformed.append(res)
    return transformed


_custom_module = 'azure.cli.command_modules.profile.custom#'

cli_command(__name__, 'account list', _custom_module + 'list_subscriptions',
            table_transformer=transform_account_list)
cli_command(__name__, 'account set', _custom_module + 'set_active_subscription')
cli_command(__name__, 'account show', _custom_module + 'show_subscription')
cli_command(__name__, 'account clear', _custom_module + 'account_clear')
cli_command(__name__, 'account list-locations', _custom_module + 'list_locations')
cli_command(__name__, 'account get-access-token', _custom_module + 'get_access_token')
