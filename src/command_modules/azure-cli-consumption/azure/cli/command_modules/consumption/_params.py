# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from ._validators import get_datetime_type
from decimal import Decimal


def load_arguments(self, _):
    with self.argument_context('consumption usage') as c:
        c.argument('top', options_list=['--top', '-t'], type=int, help='Maximum number of items to return. Value range: 1-1000.')
        c.argument('include_additional_properties', options_list=['--include-additional-properties', '-a'], action='store_true', help='Include additional properties in the usages.')
        c.argument('include_meter_details', options_list=['--include-meter-details', '-m'], action='store_true', help='Include meter details in the usages.')
        c.argument('start_date', options_list=['--start-date', '-s'], type=get_datetime_type(), help='Start date (YYYY-MM-DD in UTC). If specified, also requires --end-date.')
        c.argument('end_date', options_list=['--end-date', '-e'], type=get_datetime_type(), help='End date (YYYY-MM-DD in UTC). If specified, also requires --start-date.')
        c.argument('billing_period_name', options_list=['--billing-period-name', '-p'], help='Name of the billing period to get the usage details that associate with.')

    with self.argument_context('consumption reservation') as rs:
        rs.argument('reservation_order_id', options_list='--reservation-order-id', help='Reservation order id.')
        rs.argument('start_date', options_list=['--start-date', '-s'], type=get_datetime_type(), help='Start date (YYYY-MM-DD in UTC). Only needed for daily grain and if specified, also requires --end-date.')
        rs.argument('end_date', options_list=['--end-date', '-e'], type=get_datetime_type(), help='End date (YYYY-MM-DD in UTC). Only needed for daily grain and if specified, also requires --start-date.')
        rs.argument('reservation_id', options_list='--reservation-id', help='Reservation id.')

    with self.argument_context('consumption reservation summary list') as rs:
        rs.argument('grain', options_list='--grain', type=str, help='Reservation summary grain. Possible values are daily or monthly.')

    with self.argument_context('consumption pricesheet show') as cps:
        cps.argument('include_meter_details', options_list='--include-meter-details', action='store_true', help='Include meter details in the price sheet.')
        cps.argument('billing_period_name', options_list=['--billing-period-name', '-p'], help='Name of the billing period to get the price sheet.')

    with self.argument_context('consumption marketplace list') as cmp:
        cmp.argument('billing_period_name', options_list=['--billing-period-name', '-p'], help='Name of the billing period to get the marketplace.')
        cmp.argument('top', options_list=['--top', '-t'], type=int, help='Maximum number of items to return. Value range: 1-1000.')
        cmp.argument('start_date', options_list=['--start-date', '-s'], type=get_datetime_type(), help='Start date (YYYY-MM-DD in UTC). If specified, also requires --end-date.')
        cmp.argument('end_date', options_list=['--end-date', '-e'], type=get_datetime_type(), help='End date (YYYY-MM-DD in UTC). If specified, also requires --start-date.')

    with self.argument_context('consumption budget') as cb:
        cb.argument('resource_group_name', options_list='--resource-group-name', type=str, help='Resource group of the budget.')
        cb.argument('budget_name', options_list='--budget-name', type=str, help='Name of a budget.')
        cb.argument('category', options_list=['--category', '-c'], type=str, help='Category of the budget can be cost or usage.')
        cb.argument('amount', options_list=['--amount', '-a'], type=Decimal, help='Amount of a budget.')
        cb.argument('time_grain', options_list='--time_grain', type=str, help='Time grain of the budget can be monthly, quarterly, or annually.')
        cb.argument('start_date', options_list=['--start_date', '-s'], type=get_datetime_type(), help='Start date (YYYY-MM-DD in UTC) of time period of a budget.')
        cb.argument('end_date', options_list=['--end_date', '-e'], type=get_datetime_type(), help='End date (YYYY-MM-DD in UTC) of time period of a budget.')
        cb.argument('resource_groups', options_list='--resource-groups', nargs='+', help='Space-separated list of resource groups to filter on.')
        cb.argument('resources', options_list='--resources', nargs='+', help='Space-separated list of resource instances to filter on.')
        cb.argument('meters', options_list='--meters', nargs='+', help='Space-separated list of meters to filter on. Required if category is usage.')
