# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResultCreateModel(Model):
    """TestResultCreateModel.

    :param area:
    :type area: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param associated_work_items:
    :type associated_work_items: list of int
    :param automated_test_id:
    :type automated_test_id: str
    :param automated_test_name:
    :type automated_test_name: str
    :param automated_test_storage:
    :type automated_test_storage: str
    :param automated_test_type:
    :type automated_test_type: str
    :param automated_test_type_id:
    :type automated_test_type_id: str
    :param comment:
    :type comment: str
    :param completed_date:
    :type completed_date: str
    :param computer_name:
    :type computer_name: str
    :param configuration:
    :type configuration: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
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
    :param test_case:
    :type test_case: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param test_case_priority:
    :type test_case_priority: str
    :param test_case_title:
    :type test_case_title: str
    :param test_point:
    :type test_point: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    """

    _attribute_map = {
        'area': {'key': 'area', 'type': 'ShallowReference'},
        'associated_work_items': {'key': 'associatedWorkItems', 'type': '[int]'},
        'automated_test_id': {'key': 'automatedTestId', 'type': 'str'},
        'automated_test_name': {'key': 'automatedTestName', 'type': 'str'},
        'automated_test_storage': {'key': 'automatedTestStorage', 'type': 'str'},
        'automated_test_type': {'key': 'automatedTestType', 'type': 'str'},
        'automated_test_type_id': {'key': 'automatedTestTypeId', 'type': 'str'},
        'comment': {'key': 'comment', 'type': 'str'},
        'completed_date': {'key': 'completedDate', 'type': 'str'},
        'computer_name': {'key': 'computerName', 'type': 'str'},
        'configuration': {'key': 'configuration', 'type': 'ShallowReference'},
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
        'test_case': {'key': 'testCase', 'type': 'ShallowReference'},
        'test_case_priority': {'key': 'testCasePriority', 'type': 'str'},
        'test_case_title': {'key': 'testCaseTitle', 'type': 'str'},
        'test_point': {'key': 'testPoint', 'type': 'ShallowReference'}
    }

    def __init__(self, area=None, associated_work_items=None, automated_test_id=None, automated_test_name=None, automated_test_storage=None, automated_test_type=None, automated_test_type_id=None, comment=None, completed_date=None, computer_name=None, configuration=None, custom_fields=None, duration_in_ms=None, error_message=None, failure_type=None, outcome=None, owner=None, resolution_state=None, run_by=None, stack_trace=None, started_date=None, state=None, test_case=None, test_case_priority=None, test_case_title=None, test_point=None):
        super(TestResultCreateModel, self).__init__()
        self.area = area
        self.associated_work_items = associated_work_items
        self.automated_test_id = automated_test_id
        self.automated_test_name = automated_test_name
        self.automated_test_storage = automated_test_storage
        self.automated_test_type = automated_test_type
        self.automated_test_type_id = automated_test_type_id
        self.comment = comment
        self.completed_date = completed_date
        self.computer_name = computer_name
        self.configuration = configuration
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
        self.test_case = test_case
        self.test_case_priority = test_case_priority
        self.test_case_title = test_case_title
        self.test_point = test_point
