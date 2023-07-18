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
    BoolEqualsAdvancedFilter,
    StringNotBeginsWithAdvancedFilter,
    StringNotContainsAdvancedFilter,
    StringNotEndsWithAdvancedFilter,
    IsNullOrUndefinedAdvancedFilter,
    IsNotNullAdvancedFilter,
    NumberInRangeAdvancedFilter,
    NumberNotInRangeAdvancedFilter)

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
NUMBERINRANGE = "NumberInRange"
NUMBERNOTINRANGE = "NumberNotInRange"
STRINGNOTBEGINSWITH = "StringNotBeginsWith"
STRINGNOTENDSWITH = "StringNotEndsWith"
STRINGNOTCONTAINS = "StringNotContains"
ISNULLORUNDEFINED = "IsNullOrUndefined"
ISNOTNULL = "IsNotNull"


# pylint: disable=protected-access
# pylint: disable=too-few-public-methods
class EventSubscriptionAddFilter(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):

        _validate_min_values_len(values)
        key = values[0]
        operator = values[1]

# operators that support no value
        if operator.lower() == ISNULLORUNDEFINED.lower():
            advanced_filter = _get_zero_value_advanced_filter(key, operator, values)
        elif operator.lower() == ISNOTNULL.lower():
            advanced_filter = _get_zero_value_advanced_filter(key, operator, values)

# operators that support single value
        elif operator.lower() == NUMBERLESSTHAN.lower():
            advanced_filter = _get_single_value_advanced_filter(key, operator, values)
        elif operator.lower() == NUMBERLESSTHANOREQUALS.lower():
            advanced_filter = _get_single_value_advanced_filter(key, operator, values)
        elif operator.lower() == NUMBERGREATERTHAN.lower():
            advanced_filter = _get_single_value_advanced_filter(key, operator, values)
        elif operator.lower() == NUMBERGREATERTHANOREQUALS.lower():
            advanced_filter = _get_single_value_advanced_filter(key, operator, values)
        elif operator.lower() == BOOLEQUALS.lower():
            advanced_filter = _get_single_value_advanced_filter(key, operator, values)

# operators that support multiple values
        elif operator.lower() == NUMBERIN.lower() or operator.lower() == NUMBERNOTIN.lower():
            advanced_filter = _get_multi_value_advanced_filter(key, operator, values)
        elif operator.lower() == STRINGIN.lower():
            advanced_filter = _get_multi_value_advanced_filter(key, operator, values)
        elif operator.lower() == STRINGNOTIN.lower():
            advanced_filter = _get_multi_value_advanced_filter(key, operator, values)
        elif operator.lower() == STRINGBEGINSWITH.lower():
            advanced_filter = _get_multi_value_advanced_filter(key, operator, values)
        elif operator.lower() == STRINGNOTBEGINSWITH.lower():
            advanced_filter = _get_multi_value_advanced_filter(key, operator, values)
        elif operator.lower() == STRINGENDSWITH.lower():
            advanced_filter = _get_multi_value_advanced_filter(key, operator, values)
        elif operator.lower() == STRINGNOTENDSWITH.lower():
            advanced_filter = _get_multi_value_advanced_filter(key, operator, values)
        elif operator.lower() == STRINGCONTAINS.lower():
            advanced_filter = _get_multi_value_advanced_filter(key, operator, values)
        elif operator.lower() == STRINGNOTCONTAINS.lower():
            advanced_filter = _get_multi_value_advanced_filter(key, operator, values)

# operators that support range of values
        elif operator.lower() == NUMBERINRANGE.lower():
            advanced_filter = _get_range_advanced_filter(key, operator, values)
        elif operator.lower() == NUMBERNOTINRANGE.lower():
            advanced_filter = _get_range_advanced_filter(key, operator, values)
        else:
            raise CLIError("--advanced-filter: The specified filter operator '{}' is not"
                           " a valid operator. Supported values are ".format(operator) +
                           NUMBERIN + "," + NUMBERNOTIN + "," + STRINGIN + "," +
                           STRINGNOTIN + "," + STRINGBEGINSWITH + "," +
                           STRINGCONTAINS + "," + STRINGENDSWITH + "," +
                           NUMBERGREATERTHAN + "," + NUMBERGREATERTHANOREQUALS + "," +
                           NUMBERLESSTHAN + "," + NUMBERLESSTHANOREQUALS + "," + BOOLEQUALS + "," +
                           NUMBERINRANGE + "," + NUMBERNOTINRANGE + "," +
                           ISNULLORUNDEFINED + "," + ISNOTNULL + "," +
                           STRINGNOTBEGINSWITH + "," + STRINGNOTENDSWITH + "," +
                           STRINGNOTCONTAINS + ".")
        if namespace.advanced_filter is None:
            namespace.advanced_filter = []
        namespace.advanced_filter.append(advanced_filter)


def _get_zero_value_advanced_filter(key, operator, values):
    if len(values) != 2:
        raise CLIError("--advanced-filter: For '{}' operator no filter value "
                       "must be specified.".format(operator))

    if operator.lower() == ISNULLORUNDEFINED.lower():
        advanced_filter = IsNullOrUndefinedAdvancedFilter(key=key)
    elif operator.lower() == ISNOTNULL.lower():
        advanced_filter = IsNotNullAdvancedFilter(key=key)
    else:
        raise CLIError("--advanced-filter: The specified filter operator '{}' is not"
                       " a zero value operator. Supported operators are ".format(operator) +
                       ISNULLORUNDEFINED + "," + ISNOTNULL + ".")
    return advanced_filter


def _get_single_value_advanced_filter(key, operator, values):
    if len(values) != 3:
        raise CLIError("--advanced-filter: For '{}' operator only one filter value "
                       "must be specified.".format(operator))

    if operator.lower() == NUMBERLESSTHAN.lower():
        advanced_filter = NumberLessThanAdvancedFilter(key=key, value=float(values[2]))
    elif operator.lower() == NUMBERLESSTHANOREQUALS.lower():
        advanced_filter = NumberLessThanOrEqualsAdvancedFilter(key=key, value=float(values[2]))
    elif operator.lower() == NUMBERGREATERTHAN.lower():
        advanced_filter = NumberGreaterThanAdvancedFilter(key=key, value=float(values[2]))
    elif operator.lower() == NUMBERGREATERTHANOREQUALS.lower():
        advanced_filter = NumberGreaterThanOrEqualsAdvancedFilter(key=key, value=float(values[2]))
    elif operator.lower() == BOOLEQUALS.lower():
        advanced_filter = BoolEqualsAdvancedFilter(key=key, value=bool(values[2]))
    else:
        raise CLIError("--advanced-filter: The specified filter operator '{}' is not"
                       " a single value operator. Supported operators are ".format(operator) +
                       NUMBERLESSTHAN + "," + NUMBERLESSTHANOREQUALS + "," +
                       NUMBERGREATERTHAN + "," + NUMBERGREATERTHANOREQUALS + "," +
                       BOOLEQUALS + ".")
    return advanced_filter


def _get_multi_value_advanced_filter(key, operator, values):
    if len(values) < 3:
        raise CLIError("--advanced-filter: For '{}' operator at least one filter value "
                       "must be specified.".format(operator))

    if operator.lower() == NUMBERIN.lower():
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
    elif operator.lower() == STRINGNOTBEGINSWITH.lower():
        advanced_filter = StringNotBeginsWithAdvancedFilter(key=key, values=values[2:])
    elif operator.lower() == STRINGENDSWITH.lower():
        advanced_filter = StringEndsWithAdvancedFilter(key=key, values=values[2:])
    elif operator.lower() == STRINGNOTENDSWITH.lower():
        advanced_filter = StringNotEndsWithAdvancedFilter(key=key, values=values[2:])
    elif operator.lower() == STRINGCONTAINS.lower():
        advanced_filter = StringContainsAdvancedFilter(key=key, values=values[2:])
    elif operator.lower() == STRINGNOTCONTAINS.lower():
        advanced_filter = StringNotContainsAdvancedFilter(key=key, values=values[2:])
    else:
        raise CLIError("--advanced-filter: The specified filter operator '{}' is not "
                       " a multi-value operator. Supported operators are ".format(operator) +
                       NUMBERIN + "," + NUMBERNOTIN + "," +
                       STRINGIN + "," + STRINGNOTIN + "," +
                       STRINGBEGINSWITH + "," + STRINGNOTBEGINSWITH + "," +
                       STRINGENDSWITH + "," + STRINGNOTENDSWITH + "," +
                       STRINGCONTAINS + "," + STRINGNOTCONTAINS + ".")

    return advanced_filter


def _get_range_advanced_filter(key, operator, values):
    if len(values) < 3:
        raise CLIError("--advanced-filter: For '{}' operator at least one range filter value "
                       "like 'value1,value2' must be specified.".format(operator))

    result = []
    for value in values[2:]:
        float_value = [float(i) for i in value.split(',')]
        result.append(float_value)

    if operator.lower() == NUMBERINRANGE.lower():
        advanced_filter = NumberInRangeAdvancedFilter(key=key, values=result)
    elif operator.lower() == NUMBERNOTINRANGE.lower():
        advanced_filter = NumberNotInRangeAdvancedFilter(key=key, values=result)
    else:
        raise CLIError("--advanced-filter: The specified filter operator '{}' is not "
                       " a range value operator. Supported operators are ".format(operator) +
                       NUMBERINRANGE + "," + NUMBERNOTINRANGE + ".")

    return advanced_filter


def _validate_min_values_len(values):
    valuesLen = len(values)
    if valuesLen < 2:
        raise CLIError("usage error: --advanced-filter KEY[.INNERKEY] FILTEROPERATOR VALUE [VALUE...]")
