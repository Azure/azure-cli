# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class RunCreateModel(Model):
    """RunCreateModel.

    :param automated:
    :type automated: bool
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
    :param complete_date:
    :type complete_date: str
    :param configuration_ids:
    :type configuration_ids: list of int
    :param controller:
    :type controller: str
    :param custom_test_fields:
    :type custom_test_fields: list of :class:`CustomTestField <test.v4_1.models.CustomTestField>`
    :param dtl_aut_environment:
    :type dtl_aut_environment: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param dtl_test_environment:
    :type dtl_test_environment: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param due_date:
    :type due_date: str
    :param environment_details:
    :type environment_details: :class:`DtlEnvironmentDetails <test.v4_1.models.DtlEnvironmentDetails>`
    :param error_message:
    :type error_message: str
    :param filter:
    :type filter: :class:`RunFilter <test.v4_1.models.RunFilter>`
    :param iteration:
    :type iteration: str
    :param name:
    :type name: str
    :param owner:
    :type owner: :class:`IdentityRef <test.v4_1.models.IdentityRef>`
    :param plan:
    :type plan: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param point_ids:
    :type point_ids: list of int
    :param release_environment_uri:
    :type release_environment_uri: str
    :param release_uri:
    :type release_uri: str
    :param run_timeout:
    :type run_timeout: object
    :param source_workflow:
    :type source_workflow: str
    :param start_date:
    :type start_date: str
    :param state:
    :type state: str
    :param test_configurations_mapping:
    :type test_configurations_mapping: str
    :param test_environment_id:
    :type test_environment_id: str
    :param test_settings:
    :type test_settings: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param type:
    :type type: str
    """

    _attribute_map = {
        'automated': {'key': 'automated', 'type': 'bool'},
        'build': {'key': 'build', 'type': 'ShallowReference'},
        'build_drop_location': {'key': 'buildDropLocation', 'type': 'str'},
        'build_flavor': {'key': 'buildFlavor', 'type': 'str'},
        'build_platform': {'key': 'buildPlatform', 'type': 'str'},
        'comment': {'key': 'comment', 'type': 'str'},
        'complete_date': {'key': 'completeDate', 'type': 'str'},
        'configuration_ids': {'key': 'configurationIds', 'type': '[int]'},
        'controller': {'key': 'controller', 'type': 'str'},
        'custom_test_fields': {'key': 'customTestFields', 'type': '[CustomTestField]'},
        'dtl_aut_environment': {'key': 'dtlAutEnvironment', 'type': 'ShallowReference'},
        'dtl_test_environment': {'key': 'dtlTestEnvironment', 'type': 'ShallowReference'},
        'due_date': {'key': 'dueDate', 'type': 'str'},
        'environment_details': {'key': 'environmentDetails', 'type': 'DtlEnvironmentDetails'},
        'error_message': {'key': 'errorMessage', 'type': 'str'},
        'filter': {'key': 'filter', 'type': 'RunFilter'},
        'iteration': {'key': 'iteration', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'owner': {'key': 'owner', 'type': 'IdentityRef'},
        'plan': {'key': 'plan', 'type': 'ShallowReference'},
        'point_ids': {'key': 'pointIds', 'type': '[int]'},
        'release_environment_uri': {'key': 'releaseEnvironmentUri', 'type': 'str'},
        'release_uri': {'key': 'releaseUri', 'type': 'str'},
        'run_timeout': {'key': 'runTimeout', 'type': 'object'},
        'source_workflow': {'key': 'sourceWorkflow', 'type': 'str'},
        'start_date': {'key': 'startDate', 'type': 'str'},
        'state': {'key': 'state', 'type': 'str'},
        'test_configurations_mapping': {'key': 'testConfigurationsMapping', 'type': 'str'},
        'test_environment_id': {'key': 'testEnvironmentId', 'type': 'str'},
        'test_settings': {'key': 'testSettings', 'type': 'ShallowReference'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, automated=None, build=None, build_drop_location=None, build_flavor=None, build_platform=None, comment=None, complete_date=None, configuration_ids=None, controller=None, custom_test_fields=None, dtl_aut_environment=None, dtl_test_environment=None, due_date=None, environment_details=None, error_message=None, filter=None, iteration=None, name=None, owner=None, plan=None, point_ids=None, release_environment_uri=None, release_uri=None, run_timeout=None, source_workflow=None, start_date=None, state=None, test_configurations_mapping=None, test_environment_id=None, test_settings=None, type=None):
        super(RunCreateModel, self).__init__()
        self.automated = automated
        self.build = build
        self.build_drop_location = build_drop_location
        self.build_flavor = build_flavor
        self.build_platform = build_platform
        self.comment = comment
        self.complete_date = complete_date
        self.configuration_ids = configuration_ids
        self.controller = controller
        self.custom_test_fields = custom_test_fields
        self.dtl_aut_environment = dtl_aut_environment
        self.dtl_test_environment = dtl_test_environment
        self.due_date = due_date
        self.environment_details = environment_details
        self.error_message = error_message
        self.filter = filter
        self.iteration = iteration
        self.name = name
        self.owner = owner
        self.plan = plan
        self.point_ids = point_ids
        self.release_environment_uri = release_environment_uri
        self.release_uri = release_uri
        self.run_timeout = run_timeout
        self.source_workflow = source_workflow
        self.start_date = start_date
        self.state = state
        self.test_configurations_mapping = test_configurations_mapping
        self.test_environment_id = test_environment_id
        self.test_settings = test_settings
        self.type = type
