# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SuiteEntry(Model):
    """SuiteEntry.

    :param child_suite_id: Id of child suite in a suite
    :type child_suite_id: int
    :param sequence_number: Sequence number for the test case or child suite in the suite
    :type sequence_number: int
    :param suite_id: Id for the suite
    :type suite_id: int
    :param test_case_id: Id of a test case in a suite
    :type test_case_id: int
    """

    _attribute_map = {
        'child_suite_id': {'key': 'childSuiteId', 'type': 'int'},
        'sequence_number': {'key': 'sequenceNumber', 'type': 'int'},
        'suite_id': {'key': 'suiteId', 'type': 'int'},
        'test_case_id': {'key': 'testCaseId', 'type': 'int'}
    }

    def __init__(self, child_suite_id=None, sequence_number=None, suite_id=None, test_case_id=None):
        super(SuiteEntry, self).__init__()
        self.child_suite_id = child_suite_id
        self.sequence_number = sequence_number
        self.suite_id = suite_id
        self.test_case_id = test_case_id
