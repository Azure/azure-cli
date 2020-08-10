# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestSuite(Model):
    """TestSuite.

    :param area_uri:
    :type area_uri: str
    :param children:
    :type children: list of :class:`TestSuite <test.v4_0.models.TestSuite>`
    :param default_configurations:
    :type default_configurations: list of :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param id:
    :type id: int
    :param inherit_default_configurations:
    :type inherit_default_configurations: bool
    :param last_error:
    :type last_error: str
    :param last_populated_date:
    :type last_populated_date: datetime
    :param last_updated_by:
    :type last_updated_by: :class:`IdentityRef <test.v4_0.models.IdentityRef>`
    :param last_updated_date:
    :type last_updated_date: datetime
    :param name:
    :type name: str
    :param parent:
    :type parent: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param plan:
    :type plan: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param project:
    :type project: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param query_string:
    :type query_string: str
    :param requirement_id:
    :type requirement_id: int
    :param revision:
    :type revision: int
    :param state:
    :type state: str
    :param suites:
    :type suites: list of :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param suite_type:
    :type suite_type: str
    :param test_case_count:
    :type test_case_count: int
    :param test_cases_url:
    :type test_cases_url: str
    :param text:
    :type text: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'area_uri': {'key': 'areaUri', 'type': 'str'},
        'children': {'key': 'children', 'type': '[TestSuite]'},
        'default_configurations': {'key': 'defaultConfigurations', 'type': '[ShallowReference]'},
        'id': {'key': 'id', 'type': 'int'},
        'inherit_default_configurations': {'key': 'inheritDefaultConfigurations', 'type': 'bool'},
        'last_error': {'key': 'lastError', 'type': 'str'},
        'last_populated_date': {'key': 'lastPopulatedDate', 'type': 'iso-8601'},
        'last_updated_by': {'key': 'lastUpdatedBy', 'type': 'IdentityRef'},
        'last_updated_date': {'key': 'lastUpdatedDate', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'parent': {'key': 'parent', 'type': 'ShallowReference'},
        'plan': {'key': 'plan', 'type': 'ShallowReference'},
        'project': {'key': 'project', 'type': 'ShallowReference'},
        'query_string': {'key': 'queryString', 'type': 'str'},
        'requirement_id': {'key': 'requirementId', 'type': 'int'},
        'revision': {'key': 'revision', 'type': 'int'},
        'state': {'key': 'state', 'type': 'str'},
        'suites': {'key': 'suites', 'type': '[ShallowReference]'},
        'suite_type': {'key': 'suiteType', 'type': 'str'},
        'test_case_count': {'key': 'testCaseCount', 'type': 'int'},
        'test_cases_url': {'key': 'testCasesUrl', 'type': 'str'},
        'text': {'key': 'text', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, area_uri=None, children=None, default_configurations=None, id=None, inherit_default_configurations=None, last_error=None, last_populated_date=None, last_updated_by=None, last_updated_date=None, name=None, parent=None, plan=None, project=None, query_string=None, requirement_id=None, revision=None, state=None, suites=None, suite_type=None, test_case_count=None, test_cases_url=None, text=None, url=None):
        super(TestSuite, self).__init__()
        self.area_uri = area_uri
        self.children = children
        self.default_configurations = default_configurations
        self.id = id
        self.inherit_default_configurations = inherit_default_configurations
        self.last_error = last_error
        self.last_populated_date = last_populated_date
        self.last_updated_by = last_updated_by
        self.last_updated_date = last_updated_date
        self.name = name
        self.parent = parent
        self.plan = plan
        self.project = project
        self.query_string = query_string
        self.requirement_id = requirement_id
        self.revision = revision
        self.state = state
        self.suites = suites
        self.suite_type = suite_type
        self.test_case_count = test_case_count
        self.test_cases_url = test_cases_url
        self.text = text
        self.url = url
