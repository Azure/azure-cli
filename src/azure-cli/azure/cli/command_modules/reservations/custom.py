# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.reservations.models import (Patch,
                                            PurchaseRequest,
                                            SplitRequest,
                                            MergeRequest,
                                            SkuName,
                                            PurchaseRequestPropertiesReservedResourceProperties)


def cli_reservation_update_reservation(client, reservation_order_id, reservation_id,
                                       applied_scope_type, applied_scopes=None,
                                       instance_flexibility=None):
    if applied_scopes:
        patch = Patch(applied_scope_type=applied_scope_type,
                      applied_scopes=[applied_scopes],
                      instance_flexibility=instance_flexibility)
    else:
        patch = Patch(applied_scope_type=applied_scope_type,
                      instance_flexibility=instance_flexibility)
    return client.begin_update(reservation_order_id, reservation_id, patch)


def create_resource_id(reservation_order_id, reservation_id):
    template = '/providers/Microsoft.Capacity/reservationOrders/{0}/reservations/{1}'
    return template.format(reservation_order_id, reservation_id)


def cli_reservation_split_reservation(client, reservation_order_id,
                                      reservation_id, quantity_1, quantity_2):
    reservationToSplit = create_resource_id(
        reservation_order_id, reservation_id)
    body = SplitRequest(
        quantities=[quantity_1, quantity_2], reservation_id=reservationToSplit)
    return client.begin_split(reservation_order_id, body)


def cli_reservation_merge_reservation(client, reservation_order_id,
                                      reservation_id_1, reservation_id_2):
    body = MergeRequest(sources=[create_resource_id(reservation_order_id, reservation_id_1),
                                 create_resource_id(reservation_order_id, reservation_id_2)])
    return client.begin_merge(reservation_order_id, body)


def cli_calculate(client, sku, reserved_resource_type, billing_scope_id, term,
                  quantity, applied_scope_type, display_name, applied_scope=None,
                  renew=False, instance_flexibility=None, location=None, billing_plan=None):
    sku_name = SkuName(name=sku)
    if applied_scope:
        applied_scopes = [applied_scope]
    else:
        applied_scopes = None
    properties = PurchaseRequestPropertiesReservedResourceProperties(
        instance_flexibility=instance_flexibility)
    body = PurchaseRequest(sku=sku_name, location=location, reserved_resource_type=reserved_resource_type,
                           billing_scope_id=billing_scope_id, term=term, quantity=quantity,
                           display_name=display_name,
                           applied_scope_type=applied_scope_type,
                           applied_scopes=applied_scopes, billing_plan=billing_plan,
                           renew=renew, reserved_resource_properties=properties)
    return client.calculate(body)


def cli_purchase(client, reservation_order_id, sku, reserved_resource_type, billing_scope_id, term,
                 quantity, applied_scope_type, display_name, applied_scope=None,
                 renew=False, instance_flexibility=None, location=None, billing_plan=None):
    sku_name = SkuName(name=sku)
    if applied_scope:
        applied_scopes = [applied_scope]
    else:
        applied_scopes = None
    properties = PurchaseRequestPropertiesReservedResourceProperties(
        instance_flexibility=instance_flexibility)
    body = PurchaseRequest(sku=sku_name, location=location, reserved_resource_type=reserved_resource_type,
                           billing_scope_id=billing_scope_id, term=term, quantity=quantity, display_name=display_name,
                           applied_scope_type=applied_scope_type, applied_scopes=applied_scopes,
                           billing_plan=billing_plan,
                           renew=renew, reserved_resource_properties=properties)
    return client.begin_purchase(reservation_order_id, body)
