# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitPullRequestIteration(Model):
    """GitPullRequestIteration.

    :param _links: A collection of related REST reference links.
    :type _links: :class:`ReferenceLinks <git.v4_1.models.ReferenceLinks>`
    :param author: Author of the pull request iteration.
    :type author: :class:`IdentityRef <git.v4_1.models.IdentityRef>`
    :param change_list: Changes included with the pull request iteration.
    :type change_list: list of :class:`GitPullRequestChange <git.v4_1.models.GitPullRequestChange>`
    :param commits: The commits included with the pull request iteration.
    :type commits: list of :class:`GitCommitRef <git.v4_1.models.GitCommitRef>`
    :param common_ref_commit: The first common Git commit of the source and target refs.
    :type common_ref_commit: :class:`GitCommitRef <git.v4_1.models.GitCommitRef>`
    :param created_date: The creation date of the pull request iteration.
    :type created_date: datetime
    :param description: Description of the pull request iteration.
    :type description: str
    :param has_more_commits: Indicates if the Commits property contains a truncated list of commits in this pull request iteration.
    :type has_more_commits: bool
    :param id: ID of the pull request iteration. Iterations are created as a result of creating and pushing updates to a pull request.
    :type id: int
    :param push: The Git push information associated with this pull request iteration.
    :type push: :class:`GitPushRef <git.v4_1.models.GitPushRef>`
    :param reason: The reason for which the pull request iteration was created.
    :type reason: object
    :param source_ref_commit: The source Git commit of this iteration.
    :type source_ref_commit: :class:`GitCommitRef <git.v4_1.models.GitCommitRef>`
    :param target_ref_commit: The target Git commit of this iteration.
    :type target_ref_commit: :class:`GitCommitRef <git.v4_1.models.GitCommitRef>`
    :param updated_date: The updated date of the pull request iteration.
    :type updated_date: datetime
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'author': {'key': 'author', 'type': 'IdentityRef'},
        'change_list': {'key': 'changeList', 'type': '[GitPullRequestChange]'},
        'commits': {'key': 'commits', 'type': '[GitCommitRef]'},
        'common_ref_commit': {'key': 'commonRefCommit', 'type': 'GitCommitRef'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'description': {'key': 'description', 'type': 'str'},
        'has_more_commits': {'key': 'hasMoreCommits', 'type': 'bool'},
        'id': {'key': 'id', 'type': 'int'},
        'push': {'key': 'push', 'type': 'GitPushRef'},
        'reason': {'key': 'reason', 'type': 'object'},
        'source_ref_commit': {'key': 'sourceRefCommit', 'type': 'GitCommitRef'},
        'target_ref_commit': {'key': 'targetRefCommit', 'type': 'GitCommitRef'},
        'updated_date': {'key': 'updatedDate', 'type': 'iso-8601'}
    }

    def __init__(self, _links=None, author=None, change_list=None, commits=None, common_ref_commit=None, created_date=None, description=None, has_more_commits=None, id=None, push=None, reason=None, source_ref_commit=None, target_ref_commit=None, updated_date=None):
        super(GitPullRequestIteration, self).__init__()
        self._links = _links
        self.author = author
        self.change_list = change_list
        self.commits = commits
        self.common_ref_commit = common_ref_commit
        self.created_date = created_date
        self.description = description
        self.has_more_commits = has_more_commits
        self.id = id
        self.push = push
        self.reason = reason
        self.source_ref_commit = source_ref_commit
        self.target_ref_commit = target_ref_commit
        self.updated_date = updated_date
