# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.reservations._client_factory import reservation_mgmt_client_factory, reservation_order_mgmt_client_factory
from ._exception_handler import reservations_exception_handler

reservation_path = 'azure.mgmt.reservations.operations.reservation_operations#'
reservation_order_path = 'azure.mgmt.reservations.operations.reservation_order_operations#'
custom_path = 'azure.cli.command_modules.reservations.custom#'
reservation_client_path = 'azure.mgmt.reservations.azure_reservation_api#'


def reservation_command(*args, **kwargs):
    cli_command(*args, exception_handler=reservations_exception_handler, **kwargs)


reservation_command(__name__, 'reservations reservation-order list', reservation_order_path + 'ReservationOrderOperations.list', reservation_order_mgmt_client_factory)
reservation_command(__name__, 'reservations reservation-order show', reservation_order_path + 'ReservationOrderOperations.get', reservation_order_mgmt_client_factory)
reservation_command(__name__, 'reservations reservation-order-id list', reservation_client_path + 'AzureReservationAPI.get_applied_reservation_list', reservation_order_mgmt_client_factory)
reservation_command(__name__, 'reservations catalog show', reservation_client_path + 'AzureReservationAPI.get_catalog', reservation_order_mgmt_client_factory)
reservation_command(__name__, 'reservations reservation list', reservation_path + 'ReservationOperations.list', reservation_mgmt_client_factory)
reservation_command(__name__, 'reservations reservation show', reservation_path + 'ReservationOperations.get', reservation_mgmt_client_factory)
reservation_command(__name__, 'reservations reservation update', custom_path + 'cli_reservation_update_reservation', reservation_mgmt_client_factory)
reservation_command(__name__, 'reservations reservation split', custom_path + 'cli_reservation_split_reservation', reservation_mgmt_client_factory)
reservation_command(__name__, 'reservations reservation merge', custom_path + 'cli_reservation_merge_reservation', reservation_mgmt_client_factory)
reservation_command(__name__, 'reservations reservation list-history', reservation_path + 'ReservationOperations.list_revisions', reservation_mgmt_client_factory)
