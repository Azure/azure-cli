# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProjectInfo(Model):
    """ProjectInfo.

    :param abbreviation:
    :type abbreviation: str
    :param description:
    :type description: str
    :param id:
    :type id: str
    :param last_update_time:
    :type last_update_time: datetime
    :param name:
    :type name: str
    :param properties:
    :type properties: list of :class:`ProjectProperty <core.v4_1.models.ProjectProperty>`
    :param revision: Current revision of the project
    :type revision: long
    :param state:
    :type state: object
    :param uri:
    :type uri: str
    :param version:
    :type version: long
    :param visibility:
    :type visibility: object
    """

    _attribute_map = {
        'abbreviation': {'key': 'abbreviation', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'last_update_time': {'key': 'lastUpdateTime', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'properties': {'key': 'properties', 'type': '[ProjectProperty]'},
        'revision': {'key': 'revision', 'type': 'long'},
        'state': {'key': 'state', 'type': 'object'},
        'uri': {'key': 'uri', 'type': 'str'},
        'version': {'key': 'version', 'type': 'long'},
        'visibility': {'key': 'visibility', 'type': 'object'}
    }

    def __init__(self, abbreviation=None, description=None, id=None, last_update_time=None, name=None, properties=None, revision=None, state=None, uri=None, version=None, visibility=None):
        super(ProjectInfo, self).__init__()
        self.abbreviation = abbreviation
        self.description = description
        self.id = id
        self.last_update_time = last_update_time
        self.name = name
        self.properties = properties
        self.revision = revision
        self.state = state
        self.uri = uri
        self.version = version
        self.visibility = visibility
