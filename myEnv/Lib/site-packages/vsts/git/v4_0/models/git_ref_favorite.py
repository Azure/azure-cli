# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitRefFavorite(Model):
    """GitRefFavorite.

    :param _links:
    :type _links: :class:`ReferenceLinks <git.v4_0.models.ReferenceLinks>`
    :param id:
    :type id: int
    :param identity_id:
    :type identity_id: str
    :param name:
    :type name: str
    :param repository_id:
    :type repository_id: str
    :param type:
    :type type: object
    :param url:
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'id': {'key': 'id', 'type': 'int'},
        'identity_id': {'key': 'identityId', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'repository_id': {'key': 'repositoryId', 'type': 'str'},
        'type': {'key': 'type', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, id=None, identity_id=None, name=None, repository_id=None, type=None, url=None):
        super(GitRefFavorite, self).__init__()
        self._links = _links
        self.id = id
        self.identity_id = identity_id
        self.name = name
        self.repository_id = repository_id
        self.type = type
        self.url = url
