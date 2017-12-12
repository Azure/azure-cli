# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.reservations.models.patch import Patch
from azure.mgmt.reservations.models.split_request import SplitRequest
from azure.mgmt.reservations.models.merge_request import MergeRequest


def cli_reservation_update_reservation(client, reservation_order_id, reservation_id,
                                       applied_scope_type, applied_scopes=None):
    if applied_scopes:
        patch = Patch(applied_scope_type, [applied_scopes])
    else:
        patch = Patch(applied_scope_type)
    return client.update(reservation_order_id, reservation_id, patch)


def create_resource_id(reservation_order_id, reservation_id):
    template = '/providers/Microsoft.Capacity/reservationOrders/{0}/reservations/{1}'
    return template.format(reservation_order_id, reservation_id)


def cli_reservation_split_reservation(client, reservation_order_id, reservation_id, quantity_1, quantity_2):
    split = SplitRequest([quantity_1, quantity_2], create_resource_id(reservation_order_id, reservation_id))
    return client.split(reservation_order_id, split)


def cli_reservation_merge_reservation(client, reservation_order_id, reservation_id_1, reservation_id_2):
    merge = MergeRequest([create_resource_id(reservation_order_id, reservation_id_1),
                          create_resource_id(reservation_order_id, reservation_id_2)])
    return client.merge(reservation_order_id, merge)
