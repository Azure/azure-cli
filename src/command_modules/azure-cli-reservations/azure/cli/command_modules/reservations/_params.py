# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import register_cli_argument

register_cli_argument('reservations reservation update', 'applied_scope_type', options_list=('--applied-scope-type', '-t'), required=True)
register_cli_argument('reservations reservation update', 'applied_scopes', options_list=('--applied-scopes', '-s'))
register_cli_argument('reservations reservation split', 'quantity_1', options_list=('--quantity-1', '-1'), required=True)
register_cli_argument('reservations reservation split', 'quantity_2', options_list=('--quantity-2', '-2'), required=True)
register_cli_argument('reservations reservation merge', 'reservation_id_1', options_list=('--reservation-id-1', '-1'), required=True)
register_cli_argument('reservations reservation merge', 'reservation_id_2', options_list=('--reservation-id-2', '-2'), required=True)
