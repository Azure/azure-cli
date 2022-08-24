# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apim._client_factory import cf_subscription
from azure.cli.command_modules.apim._format import subscription_output_format
from azure.cli.command_modules.apim._exception_handler import default_exception_handler


def load_command_table(commands_loader, _):
    subscription_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#SubscriptionOperations.{}',
        client_factory=cf_subscription
    )

    subscription_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.apim.operations.subscription.custom#{}',
        client_factory=cf_subscription,
        exception_handler=default_exception_handler
    )

    with commands_loader.command_group('apim subscription', subscription_sdk, custom_command_type=subscription_custom_type, is_preview=True) as g:
        g.custom_command('create', 'create_subscription', table_transformer=subscription_output_format)
        g.custom_command('list', 'list_subscription', table_transformer=subscription_output_format, client_factory=cf_subscription)
        g.custom_show_command('show', 'get_subscription', table_transformer=subscription_output_format, client_factory=cf_subscription)
        g.custom_command('delete', 'delete_subscription', confirmation=True, table_transformer=subscription_output_format, client_factory=cf_subscription)
        g.custom_command('update', 'update_subscription', supports_no_wait=True, table_transformer=subscription_output_format)
        g.custom_command('regenerate-key', 'regenerate_key', table_transformer=subscription_output_format, client_factory=cf_subscription)

    with commands_loader.command_group('apim subscription keys', subscription_sdk, custom_command_type=subscription_custom_type, is_preview=True) as g:
        g.custom_command('regenerate', 'regenerate_key')
        g.custom_command('list', 'list_keys')
