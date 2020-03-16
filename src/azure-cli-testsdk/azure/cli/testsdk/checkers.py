# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import collections
import jmespath
from .exceptions import JMESPathCheckAssertionError


class JMESPathCheck(object):  # pylint: disable=too-few-public-methods
    def __init__(self, query, expected_result, case_sensitive=True):
        self._query = query
        self._expected_result = expected_result
        self._case_sensitive = case_sensitive

    def __call__(self, execution_result):
        json_value = execution_result.get_output_in_json()
        actual_result = None
        try:
            actual_result = jmespath.search(self._query, json_value,
                                            jmespath.Options(collections.OrderedDict))
        except jmespath.exceptions.JMESPathTypeError:
            raise JMESPathCheckAssertionError(self._query, self._expected_result, actual_result,
                                              execution_result.output)
        if self._case_sensitive:
            equals = actual_result == self._expected_result or str(actual_result) == str(self._expected_result)
        else:
            equals = actual_result == self._expected_result \
                or str(actual_result).lower() == str(self._expected_result).lower()
        if not equals:
            if actual_result:
                raise JMESPathCheckAssertionError(self._query, self._expected_result, actual_result,
                                                  execution_result.output)
            raise JMESPathCheckAssertionError(self._query, self._expected_result, 'None',
                                              execution_result.output)


class JMESPathCheckExists(object):  # pylint: disable=too-few-public-methods
    def __init__(self, query):
        self._query = query

    def __call__(self, execution_result):
        json_value = execution_result.get_output_in_json()
        actual_result = jmespath.search(self._query, json_value,
                                        jmespath.Options(collections.OrderedDict))
        if not actual_result:
            raise JMESPathCheckAssertionError(self._query, 'some value', actual_result,
                                              execution_result.output)


class JMESPathCheckNotExists(object):  # pylint: disable=too-few-public-methods
    def __init__(self, query):
        self._query = query

    def __call__(self, execution_result):
        json_value = execution_result.get_output_in_json()
        actual_result = jmespath.search(self._query, json_value,
                                        jmespath.Options(collections.OrderedDict))
        if actual_result:
            raise JMESPathCheckAssertionError(self._query, 'some value', actual_result,
                                              execution_result.output)


class JMESPathCheckGreaterThan(object):  # pylint: disable=too-few-public-methods
    def __init__(self, query, expected_result):
        self._query = query
        self._expected_result = expected_result

    def __call__(self, execution_result):
        json_value = execution_result.get_output_in_json()
        actual_result = jmespath.search(self._query, json_value,
                                        jmespath.Options(collections.OrderedDict))
        if not actual_result > self._expected_result:
            expected_result_format = "> {}".format(self._expected_result)

            if actual_result:
                raise JMESPathCheckAssertionError(self._query, expected_result_format, actual_result,
                                                  execution_result.output)
            raise JMESPathCheckAssertionError(self._query, expected_result_format, 'None',
                                              execution_result.output)


class JMESPathPatternCheck(object):  # pylint: disable=too-few-public-methods
    def __init__(self, query, expected_result):
        self._query = query
        self._expected_result = expected_result

    def __call__(self, execution_result):
        json_value = execution_result.get_output_in_json()
        actual_result = jmespath.search(self._query, json_value,
                                        jmespath.Options(collections.OrderedDict))
        if not re.match(self._expected_result, str(actual_result), re.IGNORECASE):
            raise JMESPathCheckAssertionError(self._query, self._expected_result, actual_result,
                                              execution_result.output)


class NoneCheck(object):  # pylint: disable=too-few-public-methods
    def __call__(self, execution_result):  # pylint: disable=no-self-use
        none_strings = ['[]', '{}', 'false']
        try:
            data = execution_result.output.strip()
            assert not data or data in none_strings
        except AssertionError:
            raise AssertionError("Actual value '{}' != Expected value falsy (None, '', []) or "
                                 "string in {}".format(data, none_strings))


class StringCheck(object):  # pylint: disable=too-few-public-methods
    def __init__(self, expected_result):
        self.expected_result = expected_result

    def __call__(self, execution_result):
        try:
            result = execution_result.output.strip().strip('"')
            assert result == self.expected_result
        except AssertionError:
            raise AssertionError(
                "Actual value '{}' != Expected value {}".format(result, self.expected_result))


class StringContainCheck(object):  # pylint: disable=too-few-public-methods
    def __init__(self, expected_result):
        self.expected_result = expected_result

    def __call__(self, execution_result):
        try:
            result = execution_result.output.strip('"')
            assert self.expected_result in result
        except AssertionError:
            raise AssertionError(
                "Actual value '{}' doesn't contain Expected value {}".format(result,
                                                                             self.expected_result))


class StringContainCheckIgnoreCase(object):  # pylint: disable=too-few-public-methods
    def __init__(self, expected_result):
        self.expected_result = expected_result.lower()

    def __call__(self, execution_result):
        try:
            result = execution_result.output.strip('"').lower()
            assert self.expected_result in result
        except AssertionError:
            raise AssertionError(
                "Actual value '{}' doesn't contain Expected value {}".format(result,
                                                                             self.expected_result))
