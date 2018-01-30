# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.command_modules.consumption._transformers import transform_usage_list_output
from azure.cli.command_modules.consumption._transformers import transform_reservation_summaries_list_output
from azure.cli.command_modules.consumption._transformers import transform_reservation_details_list_output
from azure.cli.command_modules.consumption._client_factory import usage_details_mgmt_client_factory
from azure.cli.command_modules.consumption._client_factory import reservations_summaries_mgmt_client_factory
from azure.cli.command_modules.consumption._client_factory import reservations_details_mgmt_client_factory

from azure.cli.command_modules.consumption._client_factory import budget_mgmt_client_factory
from azure.cli.command_modules.consumption._client_factory import marketplace_mgmt_client_factory
from azure.cli.command_modules.consumption._client_factory import pricesheet_mgmt_client_factory

from ._exception_handler import consumption_exception_handler
from ._validators import validate_both_start_end_dates
from ._validators import validate_reservations_summaries
from ._validators import validate_reservations_details


def load_command_table(self, _):

    #All method names 
    with self.command_group('consumption usage') as g:
        g.custom_command('list', 'cli_consumption_list_usage', transform=transform_usage_list_output,
                         exception_handler=consumption_exception_handler, validator=validate_both_start_end_dates, 
                         client_factory=usage_details_mgmt_client_factory)

    with self.command_group('consumption reservations summaries') as s:
        s.custom_command('list', 'cli_consumption_list_reservations_summaries', transform=transform_reservation_summaries_list_output,
                         exception_handler=consumption_exception_handler, validator=validate_reservations_summaries, client_factory=reservations_summaries_mgmt_client_factory)

    with self.command_group('consumption reservations details') as d:
        d.custom_command('list', 'cli_consumption_list_reservations_details', transform=transform_reservation_details_list_output,
                         exception_handler=consumption_exception_handler, validator=validate
                         _reservations_details, client_factory=reservations_details_mgmt_client_factory)

#command group name: 'consumption budget' (define in _help.py)
#custom command name defined here: 'cli_consumption_list_budget'
#budget data transformer referenced: transform_budget_output (_transformers.py)
#budget client factory referenced: budget_mgmt_client_factory (_client_factory.py)
    with self.command_group('consumption budget') as bd:
        g.custom_command('list', 'cli_consumption_list_budget', transform=transform_budget_output,
                         exception_handler=consumption_exception_handler, validator=validate_both_start_end_dates, 
                         client_factory=budget_mgmt_client_factory)

        g.custom_command('createorupdate', 'cli_consumption_create_or_update_budget', transform=transform_budget_output,
                         exception_handler=consumption_exception_handler, validator=validate_both_start_end_dates, 
                         client_factory=budget_mgmt_client_factory)
                 
        g.custom_command('delete', 'cli_consumption_delete_budget', transform=transform_budget_output,
                         exception_handler=consumption_exception_handler, validator=validate_both_start_end_dates, 
                         client_factory=budget_mgmt_client_factory)

#command group name: 'consumption marketplace'
#custom command name defined here: 'cli_consumption_list_marketplace'
#marketplace data transformer referenced: transform_marketplace_output (_transformers.py)
#client factory referenced for marketplace: marketplace_mgmt_client_factory (_client_factory.py)
    with self.command_group('consumption marketplace') as mp:
        g.custom_command('list', 'cli_consumption_list_marketplace', transform=transform_marketplace_output,
                         exception_handler=consumption_exception_handler, validator=validate_both_start_end_dates, 
                         client_factory=marketplace_mgmt_client_factory)
                         
#command group name: 'consumption pricesheet'
#custom command name defined here: 'cli_consumption_pricesheet'
#pricesheet data transformer referenced: transform_pricesheet_output (_transformers.py)
#client factory referenced for pricesheet: pricesheet_mgmt_client_factory (_client_factory.py)
    with self.command_group('consumption pricesheet') as pr:
        g.custom_command('pricesheet', 'cli_consumption_pricesheet', transform=transform_pricesheet_output,
                         exception_handler=consumption_exception_handler, client_factory=pricesheet_mgmt_client_factory)        

