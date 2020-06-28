# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestConfiguration(Model):
    """TestConfiguration.

    :param area: Area of the configuration
    :type area: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param description: Description of the configuration
    :type description: str
    :param id: Id of the configuration
    :type id: int
    :param is_default: Is the configuration a default for the test plans
    :type is_default: bool
    :param last_updated_by: Last Updated By  Reference
    :type last_updated_by: :class:`IdentityRef <test.v4_0.models.IdentityRef>`
    :param last_updated_date: Last Updated Data
    :type last_updated_date: datetime
    :param name: Name of the configuration
    :type name: str
    :param project: Project to which the configuration belongs
    :type project: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param revision: Revision of the the configuration
    :type revision: int
    :param state: State of the configuration
    :type state: object
    :param url: Url of Configuration Resource
    :type url: str
    :param values: Dictionary of Test Variable, Selected Value
    :type values: list of :class:`NameValuePair <test.v4_0.models.NameValuePair>`
    """

    _attribute_map = {
        'area': {'key': 'area', 'type': 'ShallowReference'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'is_default': {'key': 'isDefault', 'type': 'bool'},
        'last_updated_by': {'key': 'lastUpdatedBy', 'type': 'IdentityRef'},
        'last_updated_date': {'key': 'lastUpdatedDate', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'project': {'key': 'project', 'type': 'ShallowReference'},
        'revision': {'key': 'revision', 'type': 'int'},
        'state': {'key': 'state', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'},
        'values': {'key': 'values', 'type': '[NameValuePair]'}
    }

    def __init__(self, area=None, description=None, id=None, is_default=None, last_updated_by=None, last_updated_date=None, name=None, project=None, revision=None, state=None, url=None, values=None):
        super(TestConfiguration, self).__init__()
        self.area = area
        self.description = description
        self.id = id
        self.is_default = is_default
        self.last_updated_by = last_updated_by
        self.last_updated_date = last_updated_date
        self.name = name
        self.project = project
        self.revision = revision
        self.state = state
        self.url = url
        self.values = values
