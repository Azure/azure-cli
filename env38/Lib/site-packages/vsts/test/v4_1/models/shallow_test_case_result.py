# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ShallowTestCaseResult(Model):
    """ShallowTestCaseResult.

    :param automated_test_storage:
    :type automated_test_storage: str
    :param id:
    :type id: int
    :param is_re_run:
    :type is_re_run: bool
    :param outcome:
    :type outcome: str
    :param owner:
    :type owner: str
    :param priority:
    :type priority: int
    :param ref_id:
    :type ref_id: int
    :param run_id:
    :type run_id: int
    :param test_case_title:
    :type test_case_title: str
    """

    _attribute_map = {
        'automated_test_storage': {'key': 'automatedTestStorage', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'is_re_run': {'key': 'isReRun', 'type': 'bool'},
        'outcome': {'key': 'outcome', 'type': 'str'},
        'owner': {'key': 'owner', 'type': 'str'},
        'priority': {'key': 'priority', 'type': 'int'},
        'ref_id': {'key': 'refId', 'type': 'int'},
        'run_id': {'key': 'runId', 'type': 'int'},
        'test_case_title': {'key': 'testCaseTitle', 'type': 'str'}
    }

    def __init__(self, automated_test_storage=None, id=None, is_re_run=None, outcome=None, owner=None, priority=None, ref_id=None, run_id=None, test_case_title=None):
        super(ShallowTestCaseResult, self).__init__()
        self.automated_test_storage = automated_test_storage
        self.id = id
        self.is_re_run = is_re_run
        self.outcome = outcome
        self.owner = owner
        self.priority = priority
        self.ref_id = ref_id
        self.run_id = run_id
        self.test_case_title = test_case_title
