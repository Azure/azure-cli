# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WikiRepository(Model):
    """WikiRepository.

    :param head_commit: The head commit associated with the git repository backing up the wiki.
    :type head_commit: str
    :param id: The ID of the wiki which is same as the ID of the Git repository that it is backed by.
    :type id: str
    :param repository: The git repository that backs up the wiki.
    :type repository: :class:`GitRepository <wiki.v4_0.models.GitRepository>`
    """

    _attribute_map = {
        'head_commit': {'key': 'headCommit', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'repository': {'key': 'repository', 'type': 'GitRepository'}
    }

    def __init__(self, head_commit=None, id=None, repository=None):
        super(WikiRepository, self).__init__()
        self.head_commit = head_commit
        self.id = id
        self.repository = repository
