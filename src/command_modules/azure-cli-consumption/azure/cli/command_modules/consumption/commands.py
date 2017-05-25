# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.consumption._client_factory import usage_details_mgmt_client_factory
from azure.cli.command_modules.consumption._transformers import transform_usage_list_output
from ._exception_handler import consumption_exception_handler

cli_command(__name__, 'consumption usage list', 'azure.cli.command_modules.consumption.custom#cli_consumption_list_usage', usage_details_mgmt_client_factory, transform=transform_usage_list_output, exception_handler=consumption_exception_handler)
