# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PlanUpdateModel(Model):
    """PlanUpdateModel.

    :param area:
    :type area: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param automated_test_environment:
    :type automated_test_environment: :class:`TestEnvironment <test.v4_1.models.TestEnvironment>`
    :param automated_test_settings:
    :type automated_test_settings: :class:`TestSettings <test.v4_1.models.TestSettings>`
    :param build:
    :type build: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param build_definition:
    :type build_definition: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param configuration_ids:
    :type configuration_ids: list of int
    :param description:
    :type description: str
    :param end_date:
    :type end_date: str
    :param iteration:
    :type iteration: str
    :param manual_test_environment:
    :type manual_test_environment: :class:`TestEnvironment <test.v4_1.models.TestEnvironment>`
    :param manual_test_settings:
    :type manual_test_settings: :class:`TestSettings <test.v4_1.models.TestSettings>`
    :param name:
    :type name: str
    :param owner:
    :type owner: :class:`IdentityRef <test.v4_1.models.IdentityRef>`
    :param release_environment_definition:
    :type release_environment_definition: :class:`ReleaseEnvironmentDefinitionReference <test.v4_1.models.ReleaseEnvironmentDefinitionReference>`
    :param start_date:
    :type start_date: str
    :param state:
    :type state: str
    :param status:
    :type status: str
    """

    _attribute_map = {
        'area': {'key': 'area', 'type': 'ShallowReference'},
        'automated_test_environment': {'key': 'automatedTestEnvironment', 'type': 'TestEnvironment'},
        'automated_test_settings': {'key': 'automatedTestSettings', 'type': 'TestSettings'},
        'build': {'key': 'build', 'type': 'ShallowReference'},
        'build_definition': {'key': 'buildDefinition', 'type': 'ShallowReference'},
        'configuration_ids': {'key': 'configurationIds', 'type': '[int]'},
        'description': {'key': 'description', 'type': 'str'},
        'end_date': {'key': 'endDate', 'type': 'str'},
        'iteration': {'key': 'iteration', 'type': 'str'},
        'manual_test_environment': {'key': 'manualTestEnvironment', 'type': 'TestEnvironment'},
        'manual_test_settings': {'key': 'manualTestSettings', 'type': 'TestSettings'},
        'name': {'key': 'name', 'type': 'str'},
        'owner': {'key': 'owner', 'type': 'IdentityRef'},
        'release_environment_definition': {'key': 'releaseEnvironmentDefinition', 'type': 'ReleaseEnvironmentDefinitionReference'},
        'start_date': {'key': 'startDate', 'type': 'str'},
        'state': {'key': 'state', 'type': 'str'},
        'status': {'key': 'status', 'type': 'str'}
    }

    def __init__(self, area=None, automated_test_environment=None, automated_test_settings=None, build=None, build_definition=None, configuration_ids=None, description=None, end_date=None, iteration=None, manual_test_environment=None, manual_test_settings=None, name=None, owner=None, release_environment_definition=None, start_date=None, state=None, status=None):
        super(PlanUpdateModel, self).__init__()
        self.area = area
        self.automated_test_environment = automated_test_environment
        self.automated_test_settings = automated_test_settings
        self.build = build
        self.build_definition = build_definition
        self.configuration_ids = configuration_ids
        self.description = description
        self.end_date = end_date
        self.iteration = iteration
        self.manual_test_environment = manual_test_environment
        self.manual_test_settings = manual_test_settings
        self.name = name
        self.owner = owner
        self.release_environment_definition = release_environment_definition
        self.start_date = start_date
        self.state = state
        self.status = status
