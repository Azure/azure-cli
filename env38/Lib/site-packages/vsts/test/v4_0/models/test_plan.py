# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestPlan(Model):
    """TestPlan.

    :param area:
    :type area: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param automated_test_environment:
    :type automated_test_environment: :class:`TestEnvironment <test.v4_0.models.TestEnvironment>`
    :param automated_test_settings:
    :type automated_test_settings: :class:`TestSettings <test.v4_0.models.TestSettings>`
    :param build:
    :type build: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param build_definition:
    :type build_definition: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param client_url:
    :type client_url: str
    :param description:
    :type description: str
    :param end_date:
    :type end_date: datetime
    :param id:
    :type id: int
    :param iteration:
    :type iteration: str
    :param manual_test_environment:
    :type manual_test_environment: :class:`TestEnvironment <test.v4_0.models.TestEnvironment>`
    :param manual_test_settings:
    :type manual_test_settings: :class:`TestSettings <test.v4_0.models.TestSettings>`
    :param name:
    :type name: str
    :param owner:
    :type owner: :class:`IdentityRef <test.v4_0.models.IdentityRef>`
    :param previous_build:
    :type previous_build: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param project:
    :type project: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param release_environment_definition:
    :type release_environment_definition: :class:`ReleaseEnvironmentDefinitionReference <test.v4_0.models.ReleaseEnvironmentDefinitionReference>`
    :param revision:
    :type revision: int
    :param root_suite:
    :type root_suite: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param start_date:
    :type start_date: datetime
    :param state:
    :type state: str
    :param updated_by:
    :type updated_by: :class:`IdentityRef <test.v4_0.models.IdentityRef>`
    :param updated_date:
    :type updated_date: datetime
    :param url:
    :type url: str
    """

    _attribute_map = {
        'area': {'key': 'area', 'type': 'ShallowReference'},
        'automated_test_environment': {'key': 'automatedTestEnvironment', 'type': 'TestEnvironment'},
        'automated_test_settings': {'key': 'automatedTestSettings', 'type': 'TestSettings'},
        'build': {'key': 'build', 'type': 'ShallowReference'},
        'build_definition': {'key': 'buildDefinition', 'type': 'ShallowReference'},
        'client_url': {'key': 'clientUrl', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'end_date': {'key': 'endDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'int'},
        'iteration': {'key': 'iteration', 'type': 'str'},
        'manual_test_environment': {'key': 'manualTestEnvironment', 'type': 'TestEnvironment'},
        'manual_test_settings': {'key': 'manualTestSettings', 'type': 'TestSettings'},
        'name': {'key': 'name', 'type': 'str'},
        'owner': {'key': 'owner', 'type': 'IdentityRef'},
        'previous_build': {'key': 'previousBuild', 'type': 'ShallowReference'},
        'project': {'key': 'project', 'type': 'ShallowReference'},
        'release_environment_definition': {'key': 'releaseEnvironmentDefinition', 'type': 'ReleaseEnvironmentDefinitionReference'},
        'revision': {'key': 'revision', 'type': 'int'},
        'root_suite': {'key': 'rootSuite', 'type': 'ShallowReference'},
        'start_date': {'key': 'startDate', 'type': 'iso-8601'},
        'state': {'key': 'state', 'type': 'str'},
        'updated_by': {'key': 'updatedBy', 'type': 'IdentityRef'},
        'updated_date': {'key': 'updatedDate', 'type': 'iso-8601'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, area=None, automated_test_environment=None, automated_test_settings=None, build=None, build_definition=None, client_url=None, description=None, end_date=None, id=None, iteration=None, manual_test_environment=None, manual_test_settings=None, name=None, owner=None, previous_build=None, project=None, release_environment_definition=None, revision=None, root_suite=None, start_date=None, state=None, updated_by=None, updated_date=None, url=None):
        super(TestPlan, self).__init__()
        self.area = area
        self.automated_test_environment = automated_test_environment
        self.automated_test_settings = automated_test_settings
        self.build = build
        self.build_definition = build_definition
        self.client_url = client_url
        self.description = description
        self.end_date = end_date
        self.id = id
        self.iteration = iteration
        self.manual_test_environment = manual_test_environment
        self.manual_test_settings = manual_test_settings
        self.name = name
        self.owner = owner
        self.previous_build = previous_build
        self.project = project
        self.release_environment_definition = release_environment_definition
        self.revision = revision
        self.root_suite = root_suite
        self.start_date = start_date
        self.state = state
        self.updated_by = updated_by
        self.updated_date = updated_date
        self.url = url
