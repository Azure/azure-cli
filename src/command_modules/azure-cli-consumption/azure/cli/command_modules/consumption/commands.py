# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.command_modules.consumption._transformers import transform_usage_list_output
from ._exception_handler import consumption_exception_handler
from ._validators import validate_both_start_end_dates


def load_command_table(self, _):
    with self.command_group('consumption usage') as g:
        g.custom_command('list', 'cli_consumption_list_usage', transform=transform_usage_list_output,
                         exception_handler=consumption_exception_handler, validator=validate_both_start_end_dates)
