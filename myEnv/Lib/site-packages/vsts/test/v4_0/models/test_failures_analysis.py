# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestFailuresAnalysis(Model):
    """TestFailuresAnalysis.

    :param existing_failures:
    :type existing_failures: :class:`TestFailureDetails <test.v4_0.models.TestFailureDetails>`
    :param fixed_tests:
    :type fixed_tests: :class:`TestFailureDetails <test.v4_0.models.TestFailureDetails>`
    :param new_failures:
    :type new_failures: :class:`TestFailureDetails <test.v4_0.models.TestFailureDetails>`
    :param previous_context:
    :type previous_context: :class:`TestResultsContext <test.v4_0.models.TestResultsContext>`
    """

    _attribute_map = {
        'existing_failures': {'key': 'existingFailures', 'type': 'TestFailureDetails'},
        'fixed_tests': {'key': 'fixedTests', 'type': 'TestFailureDetails'},
        'new_failures': {'key': 'newFailures', 'type': 'TestFailureDetails'},
        'previous_context': {'key': 'previousContext', 'type': 'TestResultsContext'}
    }

    def __init__(self, existing_failures=None, fixed_tests=None, new_failures=None, previous_context=None):
        super(TestFailuresAnalysis, self).__init__()
        self.existing_failures = existing_failures
        self.fixed_tests = fixed_tests
        self.new_failures = new_failures
        self.previous_context = previous_context
