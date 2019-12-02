# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.reservations._client_factory import (
    reservation_mgmt_client_factory, reservation_order_mgmt_client_factory, base_mgmt_client_factory)
from ._exception_handler import reservations_exception_handler


def load_command_table(self, _):
    def reservations_type(*args, **kwargs):
        return CliCommandType(*args, exception_handler=reservations_exception_handler, **kwargs)

    reservations_order_sdk = reservations_type(
        operations_tmpl='azure.mgmt.reservations.operations#ReservationOrderOperations.{}',
        client_factory=reservation_order_mgmt_client_factory
    )

    reservations_sdk = reservations_type(
        operations_tmpl='azure.mgmt.reservations.operations#ReservationOperations.{}',
        client_factory=reservation_mgmt_client_factory
    )

    reservations_client_sdk = reservations_type(
        operations_tmpl='azure.mgmt.reservations#AzureReservationAPI.{}',
        client_factory=base_mgmt_client_factory
    )

    with self.command_group('reservations reservation-order', reservations_order_sdk, client_factory=reservation_order_mgmt_client_factory) as g:
        g.command('list', 'list')
        g.show_command('show', 'get')
        g.custom_command('calculate', 'cli_calculate')
        g.custom_command('purchase', 'cli_purchase')

    with self.command_group('reservations reservation', reservations_sdk) as g:
        g.command('list', 'list')
        g.show_command('show', 'get')
        g.command('list-history', 'list_revisions')
        g.custom_command('update', 'cli_reservation_update_reservation')
        g.custom_command('split', 'cli_reservation_split_reservation')
        g.custom_command('merge', 'cli_reservation_merge_reservation')

    with self.command_group('reservations reservation-order-id', reservations_client_sdk) as g:
        g.command('list', 'get_applied_reservation_list')

    with self.command_group('reservations catalog', reservations_client_sdk) as g:
        g.show_command('show', 'get_catalog')

    with self.command_group('reservations', is_preview=True):
        pass
