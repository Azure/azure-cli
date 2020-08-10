# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitRepositoryStats(Model):
    """GitRepositoryStats.

    :param active_pull_requests_count:
    :type active_pull_requests_count: int
    :param branches_count:
    :type branches_count: int
    :param commits_count:
    :type commits_count: int
    :param repository_id:
    :type repository_id: str
    """

    _attribute_map = {
        'active_pull_requests_count': {'key': 'activePullRequestsCount', 'type': 'int'},
        'branches_count': {'key': 'branchesCount', 'type': 'int'},
        'commits_count': {'key': 'commitsCount', 'type': 'int'},
        'repository_id': {'key': 'repositoryId', 'type': 'str'}
    }

    def __init__(self, active_pull_requests_count=None, branches_count=None, commits_count=None, repository_id=None):
        super(GitRepositoryStats, self).__init__()
        self.active_pull_requests_count = active_pull_requests_count
        self.branches_count = branches_count
        self.commits_count = commits_count
        self.repository_id = repository_id
