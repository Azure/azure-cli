# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class VstsInfo(Model):
    """VstsInfo.

    :param collection:
    :type collection: :class:`TeamProjectCollectionReference <git.v4_0.models.TeamProjectCollectionReference>`
    :param repository:
    :type repository: :class:`GitRepository <git.v4_0.models.GitRepository>`
    :param server_url:
    :type server_url: str
    """

    _attribute_map = {
        'collection': {'key': 'collection', 'type': 'TeamProjectCollectionReference'},
        'repository': {'key': 'repository', 'type': 'GitRepository'},
        'server_url': {'key': 'serverUrl', 'type': 'str'}
    }

    def __init__(self, collection=None, repository=None, server_url=None):
        super(VstsInfo, self).__init__()
        self.collection = collection
        self.repository = repository
        self.server_url = server_url
