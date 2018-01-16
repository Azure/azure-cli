# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=line-too-long
def load_arguments(self, _):
    with self.argument_context('reservations reservation update') as c:
        c.argument('applied_scope_type', options_list=['--applied-scope-type', '-t'])
        c.argument('applied_scopes', options_list=['--applied-scopes', '-s'])

    with self.argument_context('reservations reservation split') as c:
        c.argument('quantity_1', options_list=['--quantity-1', '-1'])
        c.argument('quantity_2', options_list=['--quantity-2', '-2'])

    with self.argument_context('reservations reservation merge') as c:
        c.argument('reservation_id_1', options_list=['--reservation-id-1', '-1'])
        c.argument('reservation_id_2', options_list=['--reservation-id-2', '-2'])
