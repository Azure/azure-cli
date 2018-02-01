# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.subscription._client_factory import (
    subscription_definitions_mgmt_client_factory)
from ._exception_handler import subscription_exception_handler


def load_command_table(self, _):
    subscription_definition_util = CliCommandType(
        operations_tmpl='azure.mgmt.subscription.operations.subscription_definitions_operations#SubscriptionDefinitionsOperations.{}',
        client_factory=subscription_definitions_mgmt_client_factory,
        exception_handler=subscription_exception_handler
    )

    with self.command_group('subscriptiondefinition', subscription_definition_util) as g:
        g.command('list', 'list')
        g.command('show', 'get')
        g.custom_command('create', 'cli_subscription_create_subscription_definition')
