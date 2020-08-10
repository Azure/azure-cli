# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GlobalGitRepositoryKey(Model):
    """GlobalGitRepositoryKey.

    :param collection_id: Team Project Collection ID of the collection for the repository.
    :type collection_id: str
    :param project_id: Team Project ID of the project for the repository.
    :type project_id: str
    :param repository_id: ID of the repository.
    :type repository_id: str
    """

    _attribute_map = {
        'collection_id': {'key': 'collectionId', 'type': 'str'},
        'project_id': {'key': 'projectId', 'type': 'str'},
        'repository_id': {'key': 'repositoryId', 'type': 'str'}
    }

    def __init__(self, collection_id=None, project_id=None, repository_id=None):
        super(GlobalGitRepositoryKey, self).__init__()
        self.collection_id = collection_id
        self.project_id = project_id
        self.repository_id = repository_id
