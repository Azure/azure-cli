# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .team_project_collection_reference import TeamProjectCollectionReference


class TeamProjectCollection(TeamProjectCollectionReference):
    """TeamProjectCollection.

    :param id: Collection Id.
    :type id: str
    :param name: Collection Name.
    :type name: str
    :param url: Collection REST Url.
    :type url: str
    :param _links: The links to other objects related to this object.
    :type _links: :class:`ReferenceLinks <core.v4_1.models.ReferenceLinks>`
    :param description: Project collection description.
    :type description: str
    :param state: Project collection state.
    :type state: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'description': {'key': 'description', 'type': 'str'},
        'state': {'key': 'state', 'type': 'str'}
    }

    def __init__(self, id=None, name=None, url=None, _links=None, description=None, state=None):
        super(TeamProjectCollection, self).__init__(id=id, name=name, url=url)
        self._links = _links
        self.description = description
        self.state = state
