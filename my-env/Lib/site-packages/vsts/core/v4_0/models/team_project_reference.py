# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TeamProjectReference(Model):
    """TeamProjectReference.

    :param abbreviation: Project abbreviation.
    :type abbreviation: str
    :param description: The project's description (if any).
    :type description: str
    :param id: Project identifier.
    :type id: str
    :param name: Project name.
    :type name: str
    :param revision: Project revision.
    :type revision: long
    :param state: Project state.
    :type state: object
    :param url: Url to the full version of the object.
    :type url: str
    :param visibility: Project visibility.
    :type visibility: object
    """

    _attribute_map = {
        'abbreviation': {'key': 'abbreviation', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'revision': {'key': 'revision', 'type': 'long'},
        'state': {'key': 'state', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'},
        'visibility': {'key': 'visibility', 'type': 'object'}
    }

    def __init__(self, abbreviation=None, description=None, id=None, name=None, revision=None, state=None, url=None, visibility=None):
        super(TeamProjectReference, self).__init__()
        self.abbreviation = abbreviation
        self.description = description
        self.id = id
        self.name = name
        self.revision = revision
        self.state = state
        self.url = url
        self.visibility = visibility
