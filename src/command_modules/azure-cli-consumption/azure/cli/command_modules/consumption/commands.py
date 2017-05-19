# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.consumption._client_factory import usage_details_mgmt_client_factory
from azure.cli.command_modules.consumption._transformers import transform_usage_list_output

usage_path = 'azure.cli.command_modules.consumption.custom#cli_consumption_list_usage'

cli_command(__name__, 'consumption usage list', usage_path, usage_details_mgmt_client_factory, transform=transform_usage_list_output)
