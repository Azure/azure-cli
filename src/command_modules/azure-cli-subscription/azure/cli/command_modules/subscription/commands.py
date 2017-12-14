# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE
from ._client_factory import cf_subscriptiondefinitions
from ._exception_handler import subscriptiondefinition_exception_handler

if not supported_api_version(PROFILE_TYPE, max_api='2017-03-09-profile'):
    custom_path = 'azure.cli.command_modules.subscription.custom#'
    subscriptiondefinition_path = 'azure.mgmt.subscription.operations.subscription_definitions_operations#SubscriptionDefinitionsOperations.'

    def subscriptiondefinition_command(*args, **kwargs):
        cli_command(*args, exception_handler=subscriptiondefinition_exception_handler, **kwargs)

    subscriptiondefinition_command(__name__, 'subscriptiondefinition list', subscriptiondefinition_path + 'list', cf_subscriptiondefinitions)
    subscriptiondefinition_command(__name__, 'subscriptiondefinition show', subscriptiondefinition_path + 'get', cf_subscriptiondefinitions)
    subscriptiondefinition_command(__name__, 'subscriptiondefinition create', custom_path + 'create_subscriptiondefinition', cf_subscriptiondefinitions)
