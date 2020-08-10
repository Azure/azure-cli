# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitCommitRef(Model):
    """GitCommitRef.

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
        'work_items': {'key': 'workItems', 'type': '[ResourceRef]'}
    }

    def __init__(self, _links=None, author=None, change_counts=None, changes=None, comment=None, comment_truncated=None, commit_id=None, committer=None, parents=None, remote_url=None, statuses=None, url=None, work_items=None):
        super(GitCommitRef, self).__init__()
        self._links = _links
        self.author = author
        self.change_counts = change_counts
        self.changes = changes
        self.comment = comment
        self.comment_truncated = comment_truncated
        self.commit_id = commit_id
        self.committer = committer
        self.parents = parents
        self.remote_url = remote_url
        self.statuses = statuses
        self.url = url
        self.work_items = work_items
