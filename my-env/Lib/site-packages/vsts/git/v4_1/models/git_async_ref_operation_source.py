# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitAsyncRefOperationSource(Model):
    """GitAsyncRefOperationSource.

    :param commit_list: A list of commits to cherry pick or revert
    :type commit_list: list of :class:`GitCommitRef <git.v4_1.models.GitCommitRef>`
    :param pull_request_id: Id of the pull request to cherry pick or revert
    :type pull_request_id: int
    """

    _attribute_map = {
        'commit_list': {'key': 'commitList', 'type': '[GitCommitRef]'},
        'pull_request_id': {'key': 'pullRequestId', 'type': 'int'}
    }

    def __init__(self, commit_list=None, pull_request_id=None):
        super(GitAsyncRefOperationSource, self).__init__()
        self.commit_list = commit_list
        self.pull_request_id = pull_request_id
