# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class RunFilter(Model):
    """RunFilter.

    :param source_filter: filter for the test case sources (test containers)
    :type source_filter: str
    :param test_case_filter: filter for the test cases
    :type test_case_filter: str
    """

    _attribute_map = {
        'source_filter': {'key': 'sourceFilter', 'type': 'str'},
        'test_case_filter': {'key': 'testCaseFilter', 'type': 'str'}
    }

    def __init__(self, source_filter=None, test_case_filter=None):
        super(RunFilter, self).__init__()
        self.source_filter = source_filter
        self.test_case_filter = test_case_filter
