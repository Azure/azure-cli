# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE
from ._client_factory import cf_subscription_definitions
from ._exception_handler import subscription_definition_exception_handler

if not supported_api_version(PROFILE_TYPE, max_api='2017-03-09-profile'):
    custom_path = 'azure.cli.command_modules.subscription.custom#'
    subscription_definition_path = 'azure.mgmt.subscription.operations.subscription_definitions_operations#SubscriptionDefinitionsOperations.'

    def subscription_definition_command(*args, **kwargs):
        cli_command(*args, exception_handler=subscription_definition_exception_handler, **kwargs)

    subscription_definition_command(__name__, 'subscriptiondefinition list', subscription_definition_path + 'list', cf_subscription_definitions)
    subscription_definition_command(__name__, 'subscriptiondefinition show', subscription_definition_path + 'get', cf_subscription_definitions)
    subscription_definition_command(__name__, 'subscriptiondefinition create', custom_path + 'create_subscription_definition', cf_subscription_definitions)
