# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AggregatedResultsDifference(Model):
    """AggregatedResultsDifference.

    :param increase_in_duration:
    :type increase_in_duration: object
    :param increase_in_failures:
    :type increase_in_failures: int
    :param increase_in_other_tests:
    :type increase_in_other_tests: int
    :param increase_in_passed_tests:
    :type increase_in_passed_tests: int
    :param increase_in_total_tests:
    :type increase_in_total_tests: int
    """

    _attribute_map = {
        'increase_in_duration': {'key': 'increaseInDuration', 'type': 'object'},
        'increase_in_failures': {'key': 'increaseInFailures', 'type': 'int'},
        'increase_in_other_tests': {'key': 'increaseInOtherTests', 'type': 'int'},
        'increase_in_passed_tests': {'key': 'increaseInPassedTests', 'type': 'int'},
        'increase_in_total_tests': {'key': 'increaseInTotalTests', 'type': 'int'}
    }

    def __init__(self, increase_in_duration=None, increase_in_failures=None, increase_in_other_tests=None, increase_in_passed_tests=None, increase_in_total_tests=None):
        super(AggregatedResultsDifference, self).__init__()
        self.increase_in_duration = increase_in_duration
        self.increase_in_failures = increase_in_failures
        self.increase_in_other_tests = increase_in_other_tests
        self.increase_in_passed_tests = increase_in_passed_tests
        self.increase_in_total_tests = increase_in_total_tests
