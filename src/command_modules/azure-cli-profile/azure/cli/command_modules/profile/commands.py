# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long
from collections import OrderedDict

from azure.cli.core.commands import cli_command

cli_command(__name__, 'login', 'azure.cli.command_modules.profile.custom#login')
cli_command(__name__, 'logout', 'azure.cli.command_modules.profile.custom#logout')

def transform_account_list(result):
    transformed = []
    for r in result:
        res = OrderedDict([('Name', r['name']), ('CloudName', r['cloudName']), \
            ('SubscriptionId', r['id']), ('State', r['state']), ('IsDefault', r['isDefault'])])
        transformed.append(res)
    return transformed


cli_command(__name__, 'account list', 'azure.cli.command_modules.profile.custom#list_subscriptions',
            table_transformer=transform_account_list)
cli_command(__name__, 'account set', 'azure.cli.command_modules.profile.custom#set_active_subscription')
cli_command(__name__, 'account show', 'azure.cli.command_modules.profile.custom#show_subscription')
cli_command(__name__, 'account clear', 'azure.cli.command_modules.profile.custom#account_clear')
cli_command(__name__, 'account list-locations', 'azure.cli.command_modules.profile.custom#list_locations')
