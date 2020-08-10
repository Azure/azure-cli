# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SuiteEntryUpdateModel(Model):
    """SuiteEntryUpdateModel.

    :param child_suite_id: Id of child suite in a suite
    :type child_suite_id: int
    :param sequence_number: Updated sequence number for the test case or child suite in the suite
    :type sequence_number: int
    :param test_case_id: Id of a test case in a suite
    :type test_case_id: int
    """

    _attribute_map = {
        'child_suite_id': {'key': 'childSuiteId', 'type': 'int'},
        'sequence_number': {'key': 'sequenceNumber', 'type': 'int'},
        'test_case_id': {'key': 'testCaseId', 'type': 'int'}
    }

    def __init__(self, child_suite_id=None, sequence_number=None, test_case_id=None):
        super(SuiteEntryUpdateModel, self).__init__()
        self.child_suite_id = child_suite_id
        self.sequence_number = sequence_number
        self.test_case_id = test_case_id
