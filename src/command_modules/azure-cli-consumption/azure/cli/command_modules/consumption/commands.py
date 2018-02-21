# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.command_modules.consumption._transformers import transform_usage_list_output
from azure.cli.command_modules.consumption._transformers import transform_reservation_summaries_list_output
from azure.cli.command_modules.consumption._transformers import transform_reservation_details_list_output
from azure.cli.command_modules.consumption._transformers import transform_pricesheet_show_output
from azure.cli.command_modules.consumption._client_factory import usage_details_mgmt_client_factory
from azure.cli.command_modules.consumption._client_factory import reservations_summaries_mgmt_client_factory
from azure.cli.command_modules.consumption._client_factory import reservations_details_mgmt_client_factory
from azure.cli.command_modules.consumption._client_factory import pricesheet_mgmt_client_factory
from ._exception_handler import consumption_exception_handler
from ._validators import validate_both_start_end_dates
from ._validators import validate_reservations_summaries


def load_command_table(self, _):
    with self.command_group('consumption usage') as g:
        g.custom_command('list', 'cli_consumption_list_usage', transform=transform_usage_list_output,
                         exception_handler=consumption_exception_handler, validator=validate_both_start_end_dates, client_factory=usage_details_mgmt_client_factory)

    with self.command_group('consumption reservations summaries') as s:
        s.custom_command('list', 'cli_consumption_list_reservations_summaries', transform=transform_reservation_summaries_list_output,
                         exception_handler=consumption_exception_handler, validator=validate_reservations_summaries, client_factory=reservations_summaries_mgmt_client_factory)

    with self.command_group('consumption reservations details') as d:
        d.custom_command('list', 'cli_consumption_list_reservations_details', transform=transform_reservation_details_list_output,
                         exception_handler=consumption_exception_handler, validator=None, client_factory=reservations_details_mgmt_client_factory)

    with self.command_group('consumption pricesheet') as p:
        p.custom_command('show', 'cli_consumption_list_pricesheet_show', transform=transform_pricesheet_show_output,
                         exception_handler=consumption_exception_handler, validator=None, client_factory=pricesheet_mgmt_client_factory)
