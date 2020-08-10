# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestPoint(Model):
    """TestPoint.

    :param assigned_to:
    :type assigned_to: :class:`IdentityRef <test.v4_1.models.IdentityRef>`
    :param automated:
    :type automated: bool
    :param comment:
    :type comment: str
    :param configuration:
    :type configuration: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param failure_type:
    :type failure_type: str
    :param id:
    :type id: int
    :param last_resolution_state_id:
    :type last_resolution_state_id: int
    :param last_result:
    :type last_result: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param last_result_details:
    :type last_result_details: :class:`LastResultDetails <test.v4_1.models.LastResultDetails>`
    :param last_result_state:
    :type last_result_state: str
    :param last_run_build_number:
    :type last_run_build_number: str
    :param last_test_run:
    :type last_test_run: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param last_updated_by:
    :type last_updated_by: :class:`IdentityRef <test.v4_1.models.IdentityRef>`
    :param last_updated_date:
    :type last_updated_date: datetime
    :param outcome:
    :type outcome: str
    :param revision:
    :type revision: int
    :param state:
    :type state: str
    :param suite:
    :type suite: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param test_case:
    :type test_case: :class:`WorkItemReference <test.v4_1.models.WorkItemReference>`
    :param test_plan:
    :type test_plan: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param url:
    :type url: str
    :param work_item_properties:
    :type work_item_properties: list of object
    """

    _attribute_map = {
        'assigned_to': {'key': 'assignedTo', 'type': 'IdentityRef'},
        'automated': {'key': 'automated', 'type': 'bool'},
        'comment': {'key': 'comment', 'type': 'str'},
        'configuration': {'key': 'configuration', 'type': 'ShallowReference'},
        'failure_type': {'key': 'failureType', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'last_resolution_state_id': {'key': 'lastResolutionStateId', 'type': 'int'},
        'last_result': {'key': 'lastResult', 'type': 'ShallowReference'},
        'last_result_details': {'key': 'lastResultDetails', 'type': 'LastResultDetails'},
        'last_result_state': {'key': 'lastResultState', 'type': 'str'},
        'last_run_build_number': {'key': 'lastRunBuildNumber', 'type': 'str'},
        'last_test_run': {'key': 'lastTestRun', 'type': 'ShallowReference'},
        'last_updated_by': {'key': 'lastUpdatedBy', 'type': 'IdentityRef'},
        'last_updated_date': {'key': 'lastUpdatedDate', 'type': 'iso-8601'},
        'outcome': {'key': 'outcome', 'type': 'str'},
        'revision': {'key': 'revision', 'type': 'int'},
        'state': {'key': 'state', 'type': 'str'},
        'suite': {'key': 'suite', 'type': 'ShallowReference'},
        'test_case': {'key': 'testCase', 'type': 'WorkItemReference'},
        'test_plan': {'key': 'testPlan', 'type': 'ShallowReference'},
        'url': {'key': 'url', 'type': 'str'},
        'work_item_properties': {'key': 'workItemProperties', 'type': '[object]'}
    }

    def __init__(self, assigned_to=None, automated=None, comment=None, configuration=None, failure_type=None, id=None, last_resolution_state_id=None, last_result=None, last_result_details=None, last_result_state=None, last_run_build_number=None, last_test_run=None, last_updated_by=None, last_updated_date=None, outcome=None, revision=None, state=None, suite=None, test_case=None, test_plan=None, url=None, work_item_properties=None):
        super(TestPoint, self).__init__()
        self.assigned_to = assigned_to
        self.automated = automated
        self.comment = comment
        self.configuration = configuration
        self.failure_type = failure_type
        self.id = id
        self.last_resolution_state_id = last_resolution_state_id
        self.last_result = last_result
        self.last_result_details = last_result_details
        self.last_result_state = last_result_state
        self.last_run_build_number = last_run_build_number
        self.last_test_run = last_test_run
        self.last_updated_by = last_updated_by
        self.last_updated_date = last_updated_date
        self.outcome = outcome
        self.revision = revision
        self.state = state
        self.suite = suite
        self.test_case = test_case
        self.test_plan = test_plan
        self.url = url
        self.work_item_properties = work_item_properties
