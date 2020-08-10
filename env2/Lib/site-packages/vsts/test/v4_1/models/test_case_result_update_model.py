# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestCaseResultUpdateModel(Model):
    """TestCaseResultUpdateModel.

    :param associated_work_items:
    :type associated_work_items: list of int
    :param automated_test_type_id:
    :type automated_test_type_id: str
    :param comment:
    :type comment: str
    :param completed_date:
    :type completed_date: str
    :param computer_name:
    :type computer_name: str
    :param custom_fields:
    :type custom_fields: list of :class:`CustomTestField <test.v4_1.models.CustomTestField>`
    :param duration_in_ms:
    :type duration_in_ms: str
    :param error_message:
    :type error_message: str
    :param failure_type:
    :type failure_type: str
    :param outcome:
    :type outcome: str
    :param owner:
    :type owner: :class:`IdentityRef <test.v4_1.models.IdentityRef>`
    :param resolution_state:
    :type resolution_state: str
    :param run_by:
    :type run_by: :class:`IdentityRef <test.v4_1.models.IdentityRef>`
    :param stack_trace:
    :type stack_trace: str
    :param started_date:
    :type started_date: str
    :param state:
    :type state: str
    :param test_case_priority:
    :type test_case_priority: str
    :param test_result:
    :type test_result: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    """

    _attribute_map = {
        'associated_work_items': {'key': 'associatedWorkItems', 'type': '[int]'},
        'automated_test_type_id': {'key': 'automatedTestTypeId', 'type': 'str'},
        'comment': {'key': 'comment', 'type': 'str'},
        'completed_date': {'key': 'completedDate', 'type': 'str'},
        'computer_name': {'key': 'computerName', 'type': 'str'},
        'custom_fields': {'key': 'customFields', 'type': '[CustomTestField]'},
        'duration_in_ms': {'key': 'durationInMs', 'type': 'str'},
        'error_message': {'key': 'errorMessage', 'type': 'str'},
        'failure_type': {'key': 'failureType', 'type': 'str'},
        'outcome': {'key': 'outcome', 'type': 'str'},
        'owner': {'key': 'owner', 'type': 'IdentityRef'},
        'resolution_state': {'key': 'resolutionState', 'type': 'str'},
        'run_by': {'key': 'runBy', 'type': 'IdentityRef'},
        'stack_trace': {'key': 'stackTrace', 'type': 'str'},
        'started_date': {'key': 'startedDate', 'type': 'str'},
        'state': {'key': 'state', 'type': 'str'},
        'test_case_priority': {'key': 'testCasePriority', 'type': 'str'},
        'test_result': {'key': 'testResult', 'type': 'ShallowReference'}
    }

    def __init__(self, associated_work_items=None, automated_test_type_id=None, comment=None, completed_date=None, computer_name=None, custom_fields=None, duration_in_ms=None, error_message=None, failure_type=None, outcome=None, owner=None, resolution_state=None, run_by=None, stack_trace=None, started_date=None, state=None, test_case_priority=None, test_result=None):
        super(TestCaseResultUpdateModel, self).__init__()
        self.associated_work_items = associated_work_items
        self.automated_test_type_id = automated_test_type_id
        self.comment = comment
        self.completed_date = completed_date
        self.computer_name = computer_name
        self.custom_fields = custom_fields
        self.duration_in_ms = duration_in_ms
        self.error_message = error_message
        self.failure_type = failure_type
        self.outcome = outcome
        self.owner = owner
        self.resolution_state = resolution_state
        self.run_by = run_by
        self.stack_trace = stack_trace
        self.started_date = started_date
        self.state = state
        self.test_case_priority = test_case_priority
        self.test_result = test_result
