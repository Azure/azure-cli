# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class RunUpdateModel(Model):
    """RunUpdateModel.

    :param build:
    :type build: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param build_drop_location:
    :type build_drop_location: str
    :param build_flavor:
    :type build_flavor: str
    :param build_platform:
    :type build_platform: str
    :param comment:
    :type comment: str
    :param completed_date:
    :type completed_date: str
    :param controller:
    :type controller: str
    :param delete_in_progress_results:
    :type delete_in_progress_results: bool
    :param dtl_aut_environment:
    :type dtl_aut_environment: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param dtl_environment:
    :type dtl_environment: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param dtl_environment_details:
    :type dtl_environment_details: :class:`DtlEnvironmentDetails <test.v4_1.models.DtlEnvironmentDetails>`
    :param due_date:
    :type due_date: str
    :param error_message:
    :type error_message: str
    :param iteration:
    :type iteration: str
    :param log_entries:
    :type log_entries: list of :class:`TestMessageLogDetails <test.v4_1.models.TestMessageLogDetails>`
    :param name:
    :type name: str
    :param release_environment_uri:
    :type release_environment_uri: str
    :param release_uri:
    :type release_uri: str
    :param source_workflow:
    :type source_workflow: str
    :param started_date:
    :type started_date: str
    :param state:
    :type state: str
    :param substate:
    :type substate: object
    :param test_environment_id:
    :type test_environment_id: str
    :param test_settings:
    :type test_settings: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    """

    _attribute_map = {
        'build': {'key': 'build', 'type': 'ShallowReference'},
        'build_drop_location': {'key': 'buildDropLocation', 'type': 'str'},
        'build_flavor': {'key': 'buildFlavor', 'type': 'str'},
        'build_platform': {'key': 'buildPlatform', 'type': 'str'},
        'comment': {'key': 'comment', 'type': 'str'},
        'completed_date': {'key': 'completedDate', 'type': 'str'},
        'controller': {'key': 'controller', 'type': 'str'},
        'delete_in_progress_results': {'key': 'deleteInProgressResults', 'type': 'bool'},
        'dtl_aut_environment': {'key': 'dtlAutEnvironment', 'type': 'ShallowReference'},
        'dtl_environment': {'key': 'dtlEnvironment', 'type': 'ShallowReference'},
        'dtl_environment_details': {'key': 'dtlEnvironmentDetails', 'type': 'DtlEnvironmentDetails'},
        'due_date': {'key': 'dueDate', 'type': 'str'},
        'error_message': {'key': 'errorMessage', 'type': 'str'},
        'iteration': {'key': 'iteration', 'type': 'str'},
        'log_entries': {'key': 'logEntries', 'type': '[TestMessageLogDetails]'},
        'name': {'key': 'name', 'type': 'str'},
        'release_environment_uri': {'key': 'releaseEnvironmentUri', 'type': 'str'},
        'release_uri': {'key': 'releaseUri', 'type': 'str'},
        'source_workflow': {'key': 'sourceWorkflow', 'type': 'str'},
        'started_date': {'key': 'startedDate', 'type': 'str'},
        'state': {'key': 'state', 'type': 'str'},
        'substate': {'key': 'substate', 'type': 'object'},
        'test_environment_id': {'key': 'testEnvironmentId', 'type': 'str'},
        'test_settings': {'key': 'testSettings', 'type': 'ShallowReference'}
    }

    def __init__(self, build=None, build_drop_location=None, build_flavor=None, build_platform=None, comment=None, completed_date=None, controller=None, delete_in_progress_results=None, dtl_aut_environment=None, dtl_environment=None, dtl_environment_details=None, due_date=None, error_message=None, iteration=None, log_entries=None, name=None, release_environment_uri=None, release_uri=None, source_workflow=None, started_date=None, state=None, substate=None, test_environment_id=None, test_settings=None):
        super(RunUpdateModel, self).__init__()
        self.build = build
        self.build_drop_location = build_drop_location
        self.build_flavor = build_flavor
        self.build_platform = build_platform
        self.comment = comment
        self.completed_date = completed_date
        self.controller = controller
        self.delete_in_progress_results = delete_in_progress_results
        self.dtl_aut_environment = dtl_aut_environment
        self.dtl_environment = dtl_environment
        self.dtl_environment_details = dtl_environment_details
        self.due_date = due_date
        self.error_message = error_message
        self.iteration = iteration
        self.log_entries = log_entries
        self.name = name
        self.release_environment_uri = release_environment_uri
        self.release_uri = release_uri
        self.source_workflow = source_workflow
        self.started_date = started_date
        self.state = state
        self.substate = substate
        self.test_environment_id = test_environment_id
        self.test_settings = test_settings
