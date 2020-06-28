# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .git_commit_ref import GitCommitRef


class GitCommit(GitCommitRef):
    """GitCommit.

    :param _links:
    :type _links: :class:`ReferenceLinks <git.v4_0.models.ReferenceLinks>`
    :param author:
    :type author: :class:`GitUserDate <git.v4_0.models.GitUserDate>`
    :param change_counts:
    :type change_counts: dict
    :param changes:
    :type changes: list of :class:`object <git.v4_0.models.object>`
    :param comment:
    :type comment: str
    :param comment_truncated:
    :type comment_truncated: bool
    :param commit_id:
    :type commit_id: str
    :param committer:
    :type committer: :class:`GitUserDate <git.v4_0.models.GitUserDate>`
    :param parents:
    :type parents: list of str
    :param remote_url:
    :type remote_url: str
    :param statuses:
    :type statuses: list of :class:`GitStatus <git.v4_0.models.GitStatus>`
    :param url:
    :type url: str
    :param work_items:
    :type work_items: list of :class:`ResourceRef <git.v4_0.models.ResourceRef>`
    :param push:
    :type push: :class:`GitPushRef <git.v4_0.models.GitPushRef>`
    :param tree_id:
    :type tree_id: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'author': {'key': 'author', 'type': 'GitUserDate'},
        'change_counts': {'key': 'changeCounts', 'type': '{int}'},
        'changes': {'key': 'changes', 'type': '[object]'},
        'comment': {'key': 'comment', 'type': 'str'},
        'comment_truncated': {'key': 'commentTruncated', 'type': 'bool'},
        'commit_id': {'key': 'commitId', 'type': 'str'},
        'committer': {'key': 'committer', 'type': 'GitUserDate'},
        'parents': {'key': 'parents', 'type': '[str]'},
        'remote_url': {'key': 'remoteUrl', 'type': 'str'},
        'statuses': {'key': 'statuses', 'type': '[GitStatus]'},
        'url': {'key': 'url', 'type': 'str'},
        'work_items': {'key': 'workItems', 'type': '[ResourceRef]'},
        'push': {'key': 'push', 'type': 'GitPushRef'},
        'tree_id': {'key': 'treeId', 'type': 'str'}
    }

    def __init__(self, _links=None, author=None, change_counts=None, changes=None, comment=None, comment_truncated=None, commit_id=None, committer=None, parents=None, remote_url=None, statuses=None, url=None, work_items=None, push=None, tree_id=None):
        super(GitCommit, self).__init__(_links=_links, author=author, change_counts=change_counts, changes=changes, comment=comment, comment_truncated=comment_truncated, commit_id=commit_id, committer=committer, parents=parents, remote_url=remote_url, statuses=statuses, url=url, work_items=work_items)
        self.push = push
        self.tree_id = tree_id
