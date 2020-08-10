# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestCaseResult(Model):
    """TestCaseResult.

    :param afn_strip_id:
    :type afn_strip_id: int
    :param area:
    :type area: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param associated_bugs:
    :type associated_bugs: list of :class:`ShallowReference <test.v4_0.models.ShallowReference>`
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
    :param build:
    :type build: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param build_reference:
    :type build_reference: :class:`BuildReference <test.v4_0.models.BuildReference>`
    :param comment:
    :type comment: str
    :param completed_date:
    :type completed_date: datetime
    :param computer_name:
    :type computer_name: str
    :param configuration:
    :type configuration: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param created_date:
    :type created_date: datetime
    :param custom_fields:
    :type custom_fields: list of :class:`CustomTestField <test.v4_0.models.CustomTestField>`
    :param duration_in_ms:
    :type duration_in_ms: float
    :param error_message:
    :type error_message: str
    :param failing_since:
    :type failing_since: :class:`FailingSince <test.v4_0.models.FailingSince>`
    :param failure_type:
    :type failure_type: str
    :param id:
    :type id: int
    :param iteration_details:
    :type iteration_details: list of :class:`TestIterationDetailsModel <test.v4_0.models.TestIterationDetailsModel>`
    :param last_updated_by:
    :type last_updated_by: :class:`IdentityRef <test.v4_0.models.IdentityRef>`
    :param last_updated_date:
    :type last_updated_date: datetime
    :param outcome:
    :type outcome: str
    :param owner:
    :type owner: :class:`IdentityRef <test.v4_0.models.IdentityRef>`
    :param priority:
    :type priority: int
    :param project:
    :type project: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param release:
    :type release: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param release_reference:
    :type release_reference: :class:`ReleaseReference <test.v4_0.models.ReleaseReference>`
    :param reset_count:
    :type reset_count: int
    :param resolution_state:
    :type resolution_state: str
    :param resolution_state_id:
    :type resolution_state_id: int
    :param revision:
    :type revision: int
    :param run_by:
    :type run_by: :class:`IdentityRef <test.v4_0.models.IdentityRef>`
    :param stack_trace:
    :type stack_trace: str
    :param started_date:
    :type started_date: datetime
    :param state:
    :type state: str
    :param test_case:
    :type test_case: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param test_case_reference_id:
    :type test_case_reference_id: int
    :param test_case_title:
    :type test_case_title: str
    :param test_plan:
    :type test_plan: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param test_point:
    :type test_point: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param test_run:
    :type test_run: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param test_suite:
    :type test_suite: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param url:
    :type url: str
    """

    _attribute_map = {
        'afn_strip_id': {'key': 'afnStripId', 'type': 'int'},
        'area': {'key': 'area', 'type': 'ShallowReference'},
        'associated_bugs': {'key': 'associatedBugs', 'type': '[ShallowReference]'},
        'automated_test_id': {'key': 'automatedTestId', 'type': 'str'},
        'automated_test_name': {'key': 'automatedTestName', 'type': 'str'},
        'automated_test_storage': {'key': 'automatedTestStorage', 'type': 'str'},
        'automated_test_type': {'key': 'automatedTestType', 'type': 'str'},
        'automated_test_type_id': {'key': 'automatedTestTypeId', 'type': 'str'},
        'build': {'key': 'build', 'type': 'ShallowReference'},
        'build_reference': {'key': 'buildReference', 'type': 'BuildReference'},
        'comment': {'key': 'comment', 'type': 'str'},
        'completed_date': {'key': 'completedDate', 'type': 'iso-8601'},
        'computer_name': {'key': 'computerName', 'type': 'str'},
        'configuration': {'key': 'configuration', 'type': 'ShallowReference'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'custom_fields': {'key': 'customFields', 'type': '[CustomTestField]'},
        'duration_in_ms': {'key': 'durationInMs', 'type': 'float'},
        'error_message': {'key': 'errorMessage', 'type': 'str'},
        'failing_since': {'key': 'failingSince', 'type': 'FailingSince'},
        'failure_type': {'key': 'failureType', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'iteration_details': {'key': 'iterationDetails', 'type': '[TestIterationDetailsModel]'},
        'last_updated_by': {'key': 'lastUpdatedBy', 'type': 'IdentityRef'},
        'last_updated_date': {'key': 'lastUpdatedDate', 'type': 'iso-8601'},
        'outcome': {'key': 'outcome', 'type': 'str'},
        'owner': {'key': 'owner', 'type': 'IdentityRef'},
        'priority': {'key': 'priority', 'type': 'int'},
        'project': {'key': 'project', 'type': 'ShallowReference'},
        'release': {'key': 'release', 'type': 'ShallowReference'},
        'release_reference': {'key': 'releaseReference', 'type': 'ReleaseReference'},
        'reset_count': {'key': 'resetCount', 'type': 'int'},
        'resolution_state': {'key': 'resolutionState', 'type': 'str'},
        'resolution_state_id': {'key': 'resolutionStateId', 'type': 'int'},
        'revision': {'key': 'revision', 'type': 'int'},
        'run_by': {'key': 'runBy', 'type': 'IdentityRef'},
        'stack_trace': {'key': 'stackTrace', 'type': 'str'},
        'started_date': {'key': 'startedDate', 'type': 'iso-8601'},
        'state': {'key': 'state', 'type': 'str'},
        'test_case': {'key': 'testCase', 'type': 'ShallowReference'},
        'test_case_reference_id': {'key': 'testCaseReferenceId', 'type': 'int'},
        'test_case_title': {'key': 'testCaseTitle', 'type': 'str'},
        'test_plan': {'key': 'testPlan', 'type': 'ShallowReference'},
        'test_point': {'key': 'testPoint', 'type': 'ShallowReference'},
        'test_run': {'key': 'testRun', 'type': 'ShallowReference'},
        'test_suite': {'key': 'testSuite', 'type': 'ShallowReference'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, afn_strip_id=None, area=None, associated_bugs=None, automated_test_id=None, automated_test_name=None, automated_test_storage=None, automated_test_type=None, automated_test_type_id=None, build=None, build_reference=None, comment=None, completed_date=None, computer_name=None, configuration=None, created_date=None, custom_fields=None, duration_in_ms=None, error_message=None, failing_since=None, failure_type=None, id=None, iteration_details=None, last_updated_by=None, last_updated_date=None, outcome=None, owner=None, priority=None, project=None, release=None, release_reference=None, reset_count=None, resolution_state=None, resolution_state_id=None, revision=None, run_by=None, stack_trace=None, started_date=None, state=None, test_case=None, test_case_reference_id=None, test_case_title=None, test_plan=None, test_point=None, test_run=None, test_suite=None, url=None):
        super(TestCaseResult, self).__init__()
        self.afn_strip_id = afn_strip_id
        self.area = area
        self.associated_bugs = associated_bugs
        self.automated_test_id = automated_test_id
        self.automated_test_name = automated_test_name
        self.automated_test_storage = automated_test_storage
        self.automated_test_type = automated_test_type
        self.automated_test_type_id = automated_test_type_id
        self.build = build
        self.build_reference = build_reference
        self.comment = comment
        self.completed_date = completed_date
        self.computer_name = computer_name
        self.configuration = configuration
        self.created_date = created_date
        self.custom_fields = custom_fields
        self.duration_in_ms = duration_in_ms
        self.error_message = error_message
        self.failing_since = failing_since
        self.failure_type = failure_type
        self.id = id
        self.iteration_details = iteration_details
        self.last_updated_by = last_updated_by
        self.last_updated_date = last_updated_date
        self.outcome = outcome
        self.owner = owner
        self.priority = priority
        self.project = project
        self.release = release
        self.release_reference = release_reference
        self.reset_count = reset_count
        self.resolution_state = resolution_state
        self.resolution_state_id = resolution_state_id
        self.revision = revision
        self.run_by = run_by
        self.stack_trace = stack_trace
        self.started_date = started_date
        self.state = state
        self.test_case = test_case
        self.test_case_reference_id = test_case_reference_id
        self.test_case_title = test_case_title
        self.test_plan = test_plan
        self.test_point = test_point
        self.test_run = test_run
        self.test_suite = test_suite
        self.url = url
