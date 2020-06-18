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
class EventChannelAddFilter(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) < 3:
            raise CLIError('usage error: --publisher-filter KEY[.INNERKEY] FILTEROPERATOR VALUE [VALUE ...]')

        key = values[0]
        operator = values[1]

# operators that support single value
        if operator.lower() == NUMBERLESSTHAN.lower():
            _validate_only_single_value_is_specified(NUMBERLESSTHAN, values)
            publisher_filter = NumberLessThanAdvancedFilter(key=key, value=float(values[2]))
        elif operator.lower() == NUMBERLESSTHANOREQUALS.lower():
            _validate_only_single_value_is_specified(NUMBERLESSTHANOREQUALS, values)
            publisher_filter = NumberLessThanOrEqualsAdvancedFilter(key=key, value=float(values[2]))
        elif operator.lower() == NUMBERGREATERTHAN.lower():
            _validate_only_single_value_is_specified(NUMBERGREATERTHAN, values)
            publisher_filter = NumberGreaterThanAdvancedFilter(key=key, value=float(values[2]))
        elif operator.lower() == NUMBERGREATERTHANOREQUALS.lower():
            _validate_only_single_value_is_specified(NUMBERGREATERTHANOREQUALS, values)
            publisher_filter = NumberGreaterThanOrEqualsAdvancedFilter(key=key, value=float(values[2]))
        elif operator.lower() == BOOLEQUALS.lower():
            _validate_only_single_value_is_specified(BOOLEQUALS, values)
            publisher_filter = BoolEqualsAdvancedFilter(key=key, value=bool(values[2]))

# operators that support multiple values
        elif operator.lower() == NUMBERIN.lower():
            float_values = [float(i) for i in values[2:]]
            publisher_filter = NumberInAdvancedFilter(key=key, values=float_values)
        elif operator.lower() == NUMBERNOTIN.lower():
            float_values = [float(i) for i in values[2:]]
            publisher_filter = NumberNotInAdvancedFilter(key=key, values=float_values)
        elif operator.lower() == STRINGIN.lower():
            publisher_filter = StringInAdvancedFilter(key=key, values=values[2:])
        elif operator.lower() == STRINGNOTIN.lower():
            publisher_filter = StringNotInAdvancedFilter(key=key, values=values[2:])
        elif operator.lower() == STRINGBEGINSWITH.lower():
            publisher_filter = StringBeginsWithAdvancedFilter(key=key, values=values[2:])
        elif operator.lower() == STRINGENDSWITH.lower():
            publisher_filter = StringEndsWithAdvancedFilter(key=key, values=values[2:])
        elif operator.lower() == STRINGCONTAINS.lower():
            publisher_filter = StringContainsAdvancedFilter(key=key, values=values[2:])
        else:
            raise CLIError("--publisher-filter: The specified filter operator '{}' is not"
                           " a valid operator. Supported values are ".format(operator) +
                           NUMBERIN + "," + NUMBERNOTIN + "," + STRINGIN + "," +
                           STRINGNOTIN + "," + STRINGBEGINSWITH + "," +
                           STRINGCONTAINS + "," + STRINGENDSWITH + "," +
                           NUMBERGREATERTHAN + "," + NUMBERGREATERTHANOREQUALS + "," +
                           NUMBERLESSTHAN + "," + NUMBERLESSTHANOREQUALS + "," + BOOLEQUALS + ".")
        if namespace.publisher_filter is None:
            namespace.publisher_filter = []
        namespace.publisher_filter.append(publisher_filter)


def _validate_only_single_value_is_specified(operator_type, values):
    if len(values) != 3:
        raise CLIError("--publisher-filter: For '{}' operator, only one filter value "
                       "must be specified.".format(operator_type))
