# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE
from azure.cli.command_modules.advisor._client_factory import \
    (recommendations_mgmt_client_factory,
     suppressions_mgmt_client_factory,
     configurations_mgmt_client_factory)

custom_path = 'azure.cli.command_modules.advisor.custom#'

cli_command(__name__, 'advisor recommendation list', custom_path + 'cli_advisor_list_recommendations', recommendations_mgmt_client_factory)