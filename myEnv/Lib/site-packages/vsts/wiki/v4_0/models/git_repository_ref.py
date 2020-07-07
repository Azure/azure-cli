# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitRepositoryRef(Model):
    """GitRepositoryRef.

    :param collection: Team Project Collection where this Fork resides
    :type collection: TeamProjectCollectionReference
    :param id:
    :type id: str
    :param name:
    :type name: str
    :param project:
    :type project: TeamProjectReference
    :param remote_url:
    :type remote_url: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'collection': {'key': 'collection', 'type': 'TeamProjectCollectionReference'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'project': {'key': 'project', 'type': 'TeamProjectReference'},
        'remote_url': {'key': 'remoteUrl', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, collection=None, id=None, name=None, project=None, remote_url=None, url=None):
        super(GitRepositoryRef, self).__init__()
        self.collection = collection
        self.id = id
        self.name = name
        self.project = project
        self.remote_url = remote_url
        self.url = url
