# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestFailureDetails(Model):
    """TestFailureDetails.

    :param count:
    :type count: int
    :param test_results:
    :type test_results: list of :class:`TestCaseResultIdentifier <test.v4_1.models.TestCaseResultIdentifier>`
    """

    _attribute_map = {
        'count': {'key': 'count', 'type': 'int'},
        'test_results': {'key': 'testResults', 'type': '[TestCaseResultIdentifier]'}
    }

    def __init__(self, count=None, test_results=None):
        super(TestFailureDetails, self).__init__()
        self.count = count
        self.test_results = test_results
