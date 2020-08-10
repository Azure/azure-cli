# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestRun(Model):
    """TestRun.

    :param build:
    :type build: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param build_configuration:
    :type build_configuration: :class:`BuildConfiguration <test.v4_0.models.BuildConfiguration>`
    :param comment:
    :type comment: str
    :param completed_date:
    :type completed_date: datetime
    :param controller:
    :type controller: str
    :param created_date:
    :type created_date: datetime
    :param custom_fields:
    :type custom_fields: list of :class:`CustomTestField <test.v4_0.models.CustomTestField>`
    :param drop_location:
    :type drop_location: str
    :param dtl_aut_environment:
    :type dtl_aut_environment: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param dtl_environment:
    :type dtl_environment: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param dtl_environment_creation_details:
    :type dtl_environment_creation_details: :class:`DtlEnvironmentDetails <test.v4_0.models.DtlEnvironmentDetails>`
    :param due_date:
    :type due_date: datetime
    :param error_message:
    :type error_message: str
    :param filter:
    :type filter: :class:`RunFilter <test.v4_0.models.RunFilter>`
    :param id:
    :type id: int
    :param incomplete_tests:
    :type incomplete_tests: int
    :param is_automated:
    :type is_automated: bool
    :param iteration:
    :type iteration: str
    :param last_updated_by:
    :type last_updated_by: :class:`IdentityRef <test.v4_0.models.IdentityRef>`
    :param last_updated_date:
    :type last_updated_date: datetime
    :param name:
    :type name: str
    :param not_applicable_tests:
    :type not_applicable_tests: int
    :param owner:
    :type owner: :class:`IdentityRef <test.v4_0.models.IdentityRef>`
    :param passed_tests:
    :type passed_tests: int
    :param phase:
    :type phase: str
    :param plan:
    :type plan: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param post_process_state:
    :type post_process_state: str
    :param project:
    :type project: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param release:
    :type release: :class:`ReleaseReference <test.v4_0.models.ReleaseReference>`
    :param release_environment_uri:
    :type release_environment_uri: str
    :param release_uri:
    :type release_uri: str
    :param revision:
    :type revision: int
    :param run_statistics:
    :type run_statistics: list of :class:`RunStatistic <test.v4_0.models.RunStatistic>`
    :param started_date:
    :type started_date: datetime
    :param state:
    :type state: str
    :param substate:
    :type substate: object
    :param test_environment:
    :type test_environment: :class:`TestEnvironment <test.v4_0.models.TestEnvironment>`
    :param test_message_log_id:
    :type test_message_log_id: int
    :param test_settings:
    :type test_settings: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param total_tests:
    :type total_tests: int
    :param unanalyzed_tests:
    :type unanalyzed_tests: int
    :param url:
    :type url: str
    :param web_access_url:
    :type web_access_url: str
    """

    _attribute_map = {
        'build': {'key': 'build', 'type': 'ShallowReference'},
        'build_configuration': {'key': 'buildConfiguration', 'type': 'BuildConfiguration'},
        'comment': {'key': 'comment', 'type': 'str'},
        'completed_date': {'key': 'completedDate', 'type': 'iso-8601'},
        'controller': {'key': 'controller', 'type': 'str'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'custom_fields': {'key': 'customFields', 'type': '[CustomTestField]'},
        'drop_location': {'key': 'dropLocation', 'type': 'str'},
        'dtl_aut_environment': {'key': 'dtlAutEnvironment', 'type': 'ShallowReference'},
        'dtl_environment': {'key': 'dtlEnvironment', 'type': 'ShallowReference'},
        'dtl_environment_creation_details': {'key': 'dtlEnvironmentCreationDetails', 'type': 'DtlEnvironmentDetails'},
        'due_date': {'key': 'dueDate', 'type': 'iso-8601'},
        'error_message': {'key': 'errorMessage', 'type': 'str'},
        'filter': {'key': 'filter', 'type': 'RunFilter'},
        'id': {'key': 'id', 'type': 'int'},
        'incomplete_tests': {'key': 'incompleteTests', 'type': 'int'},
        'is_automated': {'key': 'isAutomated', 'type': 'bool'},
        'iteration': {'key': 'iteration', 'type': 'str'},
        'last_updated_by': {'key': 'lastUpdatedBy', 'type': 'IdentityRef'},
        'last_updated_date': {'key': 'lastUpdatedDate', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'not_applicable_tests': {'key': 'notApplicableTests', 'type': 'int'},
        'owner': {'key': 'owner', 'type': 'IdentityRef'},
        'passed_tests': {'key': 'passedTests', 'type': 'int'},
        'phase': {'key': 'phase', 'type': 'str'},
        'plan': {'key': 'plan', 'type': 'ShallowReference'},
        'post_process_state': {'key': 'postProcessState', 'type': 'str'},
        'project': {'key': 'project', 'type': 'ShallowReference'},
        'release': {'key': 'release', 'type': 'ReleaseReference'},
        'release_environment_uri': {'key': 'releaseEnvironmentUri', 'type': 'str'},
        'release_uri': {'key': 'releaseUri', 'type': 'str'},
        'revision': {'key': 'revision', 'type': 'int'},
        'run_statistics': {'key': 'runStatistics', 'type': '[RunStatistic]'},
        'started_date': {'key': 'startedDate', 'type': 'iso-8601'},
        'state': {'key': 'state', 'type': 'str'},
        'substate': {'key': 'substate', 'type': 'object'},
        'test_environment': {'key': 'testEnvironment', 'type': 'TestEnvironment'},
        'test_message_log_id': {'key': 'testMessageLogId', 'type': 'int'},
        'test_settings': {'key': 'testSettings', 'type': 'ShallowReference'},
        'total_tests': {'key': 'totalTests', 'type': 'int'},
        'unanalyzed_tests': {'key': 'unanalyzedTests', 'type': 'int'},
        'url': {'key': 'url', 'type': 'str'},
        'web_access_url': {'key': 'webAccessUrl', 'type': 'str'}
    }

    def __init__(self, build=None, build_configuration=None, comment=None, completed_date=None, controller=None, created_date=None, custom_fields=None, drop_location=None, dtl_aut_environment=None, dtl_environment=None, dtl_environment_creation_details=None, due_date=None, error_message=None, filter=None, id=None, incomplete_tests=None, is_automated=None, iteration=None, last_updated_by=None, last_updated_date=None, name=None, not_applicable_tests=None, owner=None, passed_tests=None, phase=None, plan=None, post_process_state=None, project=None, release=None, release_environment_uri=None, release_uri=None, revision=None, run_statistics=None, started_date=None, state=None, substate=None, test_environment=None, test_message_log_id=None, test_settings=None, total_tests=None, unanalyzed_tests=None, url=None, web_access_url=None):
        super(TestRun, self).__init__()
        self.build = build
        self.build_configuration = build_configuration
        self.comment = comment
        self.completed_date = completed_date
        self.controller = controller
        self.created_date = created_date
        self.custom_fields = custom_fields
        self.drop_location = drop_location
        self.dtl_aut_environment = dtl_aut_environment
        self.dtl_environment = dtl_environment
        self.dtl_environment_creation_details = dtl_environment_creation_details
        self.due_date = due_date
        self.error_message = error_message
        self.filter = filter
        self.id = id
        self.incomplete_tests = incomplete_tests
        self.is_automated = is_automated
        self.iteration = iteration
        self.last_updated_by = last_updated_by
        self.last_updated_date = last_updated_date
        self.name = name
        self.not_applicable_tests = not_applicable_tests
        self.owner = owner
        self.passed_tests = passed_tests
        self.phase = phase
        self.plan = plan
        self.post_process_state = post_process_state
        self.project = project
        self.release = release
        self.release_environment_uri = release_environment_uri
        self.release_uri = release_uri
        self.revision = revision
        self.run_statistics = run_statistics
        self.started_date = started_date
        self.state = state
        self.substate = substate
        self.test_environment = test_environment
        self.test_message_log_id = test_message_log_id
        self.test_settings = test_settings
        self.total_tests = total_tests
        self.unanalyzed_tests = unanalyzed_tests
        self.url = url
        self.web_access_url = web_access_url
