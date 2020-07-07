# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestCaseResultIdentifier(Model):
    """TestCaseResultIdentifier.

    :param test_result_id:
    :type test_result_id: int
    :param test_run_id:
    :type test_run_id: int
    """

    _attribute_map = {
        'test_result_id': {'key': 'testResultId', 'type': 'int'},
        'test_run_id': {'key': 'testRunId', 'type': 'int'}
    }

    def __init__(self, test_result_id=None, test_run_id=None):
        super(TestCaseResultIdentifier, self).__init__()
        self.test_result_id = test_result_id
        self.test_run_id = test_run_id
