# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.advisor._client_factory import \
    (advisor_mgmt_client_factory,
     recommendations_mgmt_client_factory,
     suppressions_mgmt_client_factory,
     configurations_mgmt_client_factory)

custom_path = 'azure.cli.command_modules.advisor.custom#'

cli_command(
    __name__,
    'advisor recommendation generate',
    custom_path + 'cli_advisor_generate_recommendations',
    recommendations_mgmt_client_factory
)

cli_command(
    __name__,
    'advisor recommendation list',
    custom_path + 'cli_advisor_list_recommendations',
    recommendations_mgmt_client_factory
)

cli_command(
    __name__,
    'advisor recommendation disable',
    custom_path + 'cli_advisor_disable_recommendations',
    suppressions_mgmt_client_factory
)

cli_command(
    __name__,
    'advisor recommendation enable',
    custom_path + 'cli_advisor_enable_recommendations',
    advisor_mgmt_client_factory  # using advisor client here because this spans recommendations and suppressions
)

cli_command(
    __name__,
    'advisor configuration get',
    custom_path + 'cli_advisor_get_configurations',
    configurations_mgmt_client_factory
)

cli_command(
    __name__,
    'advisor configuration set',
    custom_path + 'cli_advisor_set_configurations',
    configurations_mgmt_client_factory
)
