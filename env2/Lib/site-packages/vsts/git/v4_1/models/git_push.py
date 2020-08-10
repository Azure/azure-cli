# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .git_push_ref import GitPushRef


class GitPush(GitPushRef):
    """GitPush.

    :param _links:
    :type _links: :class:`ReferenceLinks <git.v4_1.models.ReferenceLinks>`
    :param date:
    :type date: datetime
    :param push_correlation_id:
    :type push_correlation_id: str
    :param pushed_by:
    :type pushed_by: :class:`IdentityRef <git.v4_1.models.IdentityRef>`
    :param push_id:
    :type push_id: int
    :param url:
    :type url: str
    :param commits:
    :type commits: list of :class:`GitCommitRef <git.v4_1.models.GitCommitRef>`
    :param ref_updates:
    :type ref_updates: list of :class:`GitRefUpdate <git.v4_1.models.GitRefUpdate>`
    :param repository:
    :type repository: :class:`GitRepository <git.v4_1.models.GitRepository>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'date': {'key': 'date', 'type': 'iso-8601'},
        'push_correlation_id': {'key': 'pushCorrelationId', 'type': 'str'},
        'pushed_by': {'key': 'pushedBy', 'type': 'IdentityRef'},
        'push_id': {'key': 'pushId', 'type': 'int'},
        'url': {'key': 'url', 'type': 'str'},
        'commits': {'key': 'commits', 'type': '[GitCommitRef]'},
        'ref_updates': {'key': 'refUpdates', 'type': '[GitRefUpdate]'},
        'repository': {'key': 'repository', 'type': 'GitRepository'}
    }

    def __init__(self, _links=None, date=None, push_correlation_id=None, pushed_by=None, push_id=None, url=None, commits=None, ref_updates=None, repository=None):
        super(GitPush, self).__init__(_links=_links, date=date, push_correlation_id=push_correlation_id, pushed_by=pushed_by, push_id=push_id, url=url)
        self.commits = commits
        self.ref_updates = ref_updates
        self.repository = repository
