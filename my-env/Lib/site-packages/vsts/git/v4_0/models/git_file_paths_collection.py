# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitFilePathsCollection(Model):
    """GitFilePathsCollection.

    :param commit_id:
    :type commit_id: str
    :param paths:
    :type paths: list of str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'commit_id': {'key': 'commitId', 'type': 'str'},
        'paths': {'key': 'paths', 'type': '[str]'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, commit_id=None, paths=None, url=None):
        super(GitFilePathsCollection, self).__init__()
        self.commit_id = commit_id
        self.paths = paths
        self.url = url
