# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from azure.cli.core.commands.parameters import (get_enum_type, get_three_state_flag)

from azure.mgmt.reservations.models import (
    ReservedResourceType,
    InstanceFlexibility,
    AppliedScopeType,
    ReservationBillingPlan,
    ReservationTerm
)


def load_arguments(self, _):
    from knack.arguments import CLIArgumentType

    billing_scope_id_type = CLIArgumentType(
        options_list=['--billing-scope'],
        help='Subscription that will be charged for purchasing Reservation.')
    sku_type = CLIArgumentType(
        options_list=['--sku'],
        help='Sku name, get the sku list by using command az reservations catalog show')
    display_name_type = CLIArgumentType(
        options_list=['--display-name'],
        help='Friendly name for user to easily identified the reservation.')
    term_type = CLIArgumentType(
        options_list=['--term'],
        help='Available reservation terms for this resource.',
        arg_type=get_enum_type(ReservationTerm))
    renew_type = CLIArgumentType(
        options_list=['--renew'],
        help='Set this to true will automatically purchase a new reservation on the expiration date time.',
        arg_type=get_three_state_flag())
    billing_plan_type = CLIArgumentType(
        options_list=['--billing-plan'],
        help='The billing plan options available for this SKU.',
        arg_type=get_enum_type(ReservationBillingPlan))
    instance_flexibility_type = CLIArgumentType(
        options_list=['--instance-flexibility'],
        help='Type of the Instance Flexibility to update the reservation with.')
    applied_scope_type_param_type = CLIArgumentType(
        options_list=['--applied-scope-type'],
        help='Type of the Applied Scope to update the reservation with',
        arg_type=get_enum_type(AppliedScopeType))
    applied_scope_param_type = CLIArgumentType(
        options_list=['--applied-scope'],
        help='Subscription that the benefit will be applied. Required if --applied-scope-type is Single. Do not specify if --applied-scope-type is Shared.')
    quantity_type = CLIArgumentType(
        options_list=['--quantity'],
        help='Quantity of product for calculating price or purchasing.'
    )
    reservation_resource_type_param_type = CLIArgumentType(
        options_list=['--reserved-resource-type'],
        help='Type of the resource for which the skus should be provided.',
        arg_type=get_enum_type(ReservedResourceType)
    )

    with self.argument_context('reservations reservation update') as c:
        c.argument('applied_scope_type', options_list=['--applied-scope-type', '-t'], arg_type=get_enum_type(AppliedScopeType))
        c.argument('applied_scopes', options_list=['--applied-scopes', '-s'])
        c.argument('instance_flexibility', options_list=['--instance-flexibility', '-i'], arg_type=get_enum_type(InstanceFlexibility))

    with self.argument_context('reservations reservation split') as c:
        c.argument('quantity_1', options_list=['--quantity-1', '-1'])
        c.argument('quantity_2', options_list=['--quantity-2', '-2'])

    with self.argument_context('reservations reservation merge') as c:
        c.argument('reservation_id_1', options_list=['--reservation-id-1', '-1'])
        c.argument('reservation_id_2', options_list=['--reservation-id-2', '-2'])

    with self.argument_context('reservations catalog show') as c:
        c.argument('reserved_resource_type', arg_type=get_enum_type(ReservedResourceType))

    with self.argument_context('reservations reservation-order calculate') as c:
        c.argument('billing_scope_id', billing_scope_id_type)
        c.argument('instance_flexibility', instance_flexibility_type)
        c.argument('renew', renew_type)
        c.argument('reserved_resource_type', reservation_resource_type_param_type)
        c.argument('applied_scope_type', applied_scope_type_param_type)
        c.argument('billing_plan', billing_plan_type)
        c.argument('term', term_type)
        c.argument('display_name', display_name_type)
        c.argument('sku', sku_type)
        c.argument('applied_scope', applied_scope_param_type)
        c.argument('quantity', quantity_type)
        c.argument('location', options_list=['--location'], help='Values from: `az account list-locations`.')

    with self.argument_context('reservations reservation-order purchase') as c:
        c.argument('reservation_order_id', help='Id of reservation order to purchase, generate by `az reservations reservation-order calculate`.')
        c.argument('billing_scope_id', billing_scope_id_type)
        c.argument('instance_flexibility', instance_flexibility_type)
        c.argument('renew', renew_type)
        c.argument('reserved_resource_type', reservation_resource_type_param_type)
        c.argument('applied_scope_type', applied_scope_type_param_type)
        c.argument('billing_plan', billing_plan_type)
        c.argument('term', term_type)
        c.argument('display_name', display_name_type)
        c.argument('sku', sku_type)
        c.argument('applied_scope', applied_scope_param_type)
        c.argument('quantity', quantity_type)
        c.argument('location', options_list=['--location'], help='Values from: `az account list-locations`.')
