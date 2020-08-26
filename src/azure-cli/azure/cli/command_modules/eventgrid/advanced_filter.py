# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
from knack.util import CLIError

from azure.mgmt.eventgrid.models import (
    NumberGreaterThanAdvancedFilter,
    NumberGreaterThanOrEqualsAdvancedFilter,
    NumberInAdvancedFilter,
    NumberLessThanAdvancedFilter,
    NumberLessThanOrEqualsAdvancedFilter,
    NumberNotInAdvancedFilter,
    StringBeginsWithAdvancedFilter,
    StringContainsAdvancedFilter,
    StringEndsWithAdvancedFilter,
    StringInAdvancedFilter,
    StringNotInAdvancedFilter,
    BoolEqualsAdvancedFilter)

NUMBERIN = "NumberIn"
NUMBERNOTIN = "NumberNotIn"
STRINGIN = "StringIn"
STRINGNOTIN = "StringNotIn"
STRINGBEGINSWITH = "StringBeginsWith"
STRINGCONTAINS = "StringContains"
STRINGENDSWITH = "StringEndsWith"
NUMBERGREATERTHAN = "NumberGreaterThan"
NUMBERGREATERTHANOREQUALS = "NumberGreaterThanOrEquals"
NUMBERLESSTHAN = "NumberLessThan"
NUMBERLESSTHANOREQUALS = "NumberLessThanOrEquals"
BOOLEQUALS = "BoolEquals"


# pylint: disable=protected-access
# pylint: disable=too-few-public-methods
class EventSubscriptionAddFilter(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) < 3:
            raise CLIError('usage error: --advanced-filter KEY[.INNERKEY] FILTEROPERATOR VALUE [VALUE ...]')

        key = values[0]
        operator = values[1]

# operators that support single value
        if operator.lower() == NUMBERLESSTHAN.lower():
            _validate_only_single_value_is_specified(NUMBERLESSTHAN, values)
            advanced_filter = NumberLessThanAdvancedFilter(key=key, value=float(values[2]))
        elif operator.lower() == NUMBERLESSTHANOREQUALS.lower():
            _validate_only_single_value_is_specified(NUMBERLESSTHANOREQUALS, values)
            advanced_filter = NumberLessThanOrEqualsAdvancedFilter(key=key, value=float(values[2]))
        elif operator.lower() == NUMBERGREATERTHAN.lower():
            _validate_only_single_value_is_specified(NUMBERGREATERTHAN, values)
            advanced_filter = NumberGreaterThanAdvancedFilter(key=key, value=float(values[2]))
        elif operator.lower() == NUMBERGREATERTHANOREQUALS.lower():
            _validate_only_single_value_is_specified(NUMBERGREATERTHANOREQUALS, values)
            advanced_filter = NumberGreaterThanOrEqualsAdvancedFilter(key=key, value=float(values[2]))
        elif operator.lower() == BOOLEQUALS.lower():
            _validate_only_single_value_is_specified(BOOLEQUALS, values)
            advanced_filter = BoolEqualsAdvancedFilter(key=key, value=bool(values[2]))

# operators that support multiple values
        elif operator.lower() == NUMBERIN.lower():
            float_values = [float(i) for i in values[2:]]
            advanced_filter = NumberInAdvancedFilter(key=key, values=float_values)
        elif operator.lower() == NUMBERNOTIN.lower():
            float_values = [float(i) for i in values[2:]]
            advanced_filter = NumberNotInAdvancedFilter(key=key, values=float_values)
        elif operator.lower() == STRINGIN.lower():
            advanced_filter = StringInAdvancedFilter(key=key, values=values[2:])
        elif operator.lower() == STRINGNOTIN.lower():
            advanced_filter = StringNotInAdvancedFilter(key=key, values=values[2:])
        elif operator.lower() == STRINGBEGINSWITH.lower():
            advanced_filter = StringBeginsWithAdvancedFilter(key=key, values=values[2:])
        elif operator.lower() == STRINGENDSWITH.lower():
            advanced_filter = StringEndsWithAdvancedFilter(key=key, values=values[2:])
        elif operator.lower() == STRINGCONTAINS.lower():
            advanced_filter = StringContainsAdvancedFilter(key=key, values=values[2:])
        else:
            raise CLIError("--advanced-filter: The specified filter operator '{}' is not"
                           " a valid operator. Supported values are ".format(operator) +
                           NUMBERIN + "," + NUMBERNOTIN + "," + STRINGIN + "," +
                           STRINGNOTIN + "," + STRINGBEGINSWITH + "," +
                           STRINGCONTAINS + "," + STRINGENDSWITH + "," +
                           NUMBERGREATERTHAN + "," + NUMBERGREATERTHANOREQUALS + "," +
                           NUMBERLESSTHAN + "," + NUMBERLESSTHANOREQUALS + "," + BOOLEQUALS + ".")
        if namespace.advanced_filter is None:
            namespace.advanced_filter = []
        namespace.advanced_filter.append(advanced_filter)


def _validate_only_single_value_is_specified(operator_type, values):
    if len(values) != 3:
        raise CLIError("--advanced-filter: For '{}' operator, only one filter value "
                       "must be specified.".format(operator_type))
