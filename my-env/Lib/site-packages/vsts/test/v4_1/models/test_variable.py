# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestVariable(Model):
    """TestVariable.

    :param description: Description of the test variable
    :type description: str
    :param id: Id of the test variable
    :type id: int
    :param name: Name of the test variable
    :type name: str
    :param project: Project to which the test variable belongs
    :type project: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param revision: Revision
    :type revision: int
    :param url: Url of the test variable
    :type url: str
    :param values: List of allowed values
    :type values: list of str
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'},
        'project': {'key': 'project', 'type': 'ShallowReference'},
        'revision': {'key': 'revision', 'type': 'int'},
        'url': {'key': 'url', 'type': 'str'},
        'values': {'key': 'values', 'type': '[str]'}
    }

    def __init__(self, description=None, id=None, name=None, project=None, revision=None, url=None, values=None):
        super(TestVariable, self).__init__()
        self.description = description
        self.id = id
        self.name = name
        self.project = project
        self.revision = revision
        self.url = url
        self.values = values
