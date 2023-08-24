# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements
from azure.cli.core.commands.parameters import get_enum_type
from ._validators import (datetime_type,
                          decimal_type)


def load_arguments(self, _):
    with self.argument_context('consumption budget') as cb:
        cb.argument('budget_name', help='Name of a budget.')
        cb.argument('category', arg_type=get_enum_type(['cost', 'usage']), help='Category of the budget can be cost or usage.')
        cb.argument('amount', type=decimal_type, help='Amount of a budget.')
        cb.argument('time_grain', arg_type=get_enum_type(['monthly', 'quarterly', 'annually']), help='Time grain of the budget can be monthly, quarterly, or annually.')
        cb.argument('start_date', options_list=['--start-date', '-s'], type=datetime_type, help='Start date (YYYY-MM-DD in UTC) of time period of a budget.')
        cb.argument('end_date', options_list=['--end-date', '-e'], type=datetime_type, help='End date (YYYY-MM-DD in UTC) of time period of a budget.')
        cb.argument('resource_groups', options_list='--resource-group-filter', nargs='+', help='Space-separated list of resource groups to filter on.')
        cb.argument('resources', options_list='--resource-filter', nargs='+', help='Space-separated list of resource instances to filter on.')
        cb.argument('meters', options_list='--meter-filter', nargs='+', help='Space-separated list of meters to filter on. Required if category is usage.')
