# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitPullRequest(Model):
    """GitPullRequest.

    :param _links:
    :type _links: :class:`ReferenceLinks <git.v4_0.models.ReferenceLinks>`
    :param artifact_id:
    :type artifact_id: str
    :param auto_complete_set_by:
    :type auto_complete_set_by: :class:`IdentityRef <git.v4_0.models.IdentityRef>`
    :param closed_by:
    :type closed_by: :class:`IdentityRef <git.v4_0.models.IdentityRef>`
    :param closed_date:
    :type closed_date: datetime
    :param code_review_id:
    :type code_review_id: int
    :param commits:
    :type commits: list of :class:`GitCommitRef <git.v4_0.models.GitCommitRef>`
    :param completion_options:
    :type completion_options: :class:`GitPullRequestCompletionOptions <git.v4_0.models.GitPullRequestCompletionOptions>`
    :param completion_queue_time:
    :type completion_queue_time: datetime
    :param created_by:
    :type created_by: :class:`IdentityRef <git.v4_0.models.IdentityRef>`
    :param creation_date:
    :type creation_date: datetime
    :param description:
    :type description: str
    :param fork_source:
    :type fork_source: :class:`GitForkRef <git.v4_0.models.GitForkRef>`
    :param labels:
    :type labels: list of :class:`WebApiTagDefinition <git.v4_0.models.WebApiTagDefinition>`
    :param last_merge_commit:
    :type last_merge_commit: :class:`GitCommitRef <git.v4_0.models.GitCommitRef>`
    :param last_merge_source_commit:
    :type last_merge_source_commit: :class:`GitCommitRef <git.v4_0.models.GitCommitRef>`
    :param last_merge_target_commit:
    :type last_merge_target_commit: :class:`GitCommitRef <git.v4_0.models.GitCommitRef>`
    :param merge_failure_message:
    :type merge_failure_message: str
    :param merge_failure_type:
    :type merge_failure_type: object
    :param merge_id:
    :type merge_id: str
    :param merge_options:
    :type merge_options: :class:`GitPullRequestMergeOptions <git.v4_0.models.GitPullRequestMergeOptions>`
    :param merge_status:
    :type merge_status: object
    :param pull_request_id:
    :type pull_request_id: int
    :param remote_url:
    :type remote_url: str
    :param repository:
    :type repository: :class:`GitRepository <git.v4_0.models.GitRepository>`
    :param reviewers:
    :type reviewers: list of :class:`IdentityRefWithVote <git.v4_0.models.IdentityRefWithVote>`
    :param source_ref_name:
    :type source_ref_name: str
    :param status:
    :type status: object
    :param supports_iterations:
    :type supports_iterations: bool
    :param target_ref_name:
    :type target_ref_name: str
    :param title:
    :type title: str
    :param url:
    :type url: str
    :param work_item_refs:
    :type work_item_refs: list of :class:`ResourceRef <git.v4_0.models.ResourceRef>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'artifact_id': {'key': 'artifactId', 'type': 'str'},
        'auto_complete_set_by': {'key': 'autoCompleteSetBy', 'type': 'IdentityRef'},
        'closed_by': {'key': 'closedBy', 'type': 'IdentityRef'},
        'closed_date': {'key': 'closedDate', 'type': 'iso-8601'},
        'code_review_id': {'key': 'codeReviewId', 'type': 'int'},
        'commits': {'key': 'commits', 'type': '[GitCommitRef]'},
        'completion_options': {'key': 'completionOptions', 'type': 'GitPullRequestCompletionOptions'},
        'completion_queue_time': {'key': 'completionQueueTime', 'type': 'iso-8601'},
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'creation_date': {'key': 'creationDate', 'type': 'iso-8601'},
        'description': {'key': 'description', 'type': 'str'},
        'fork_source': {'key': 'forkSource', 'type': 'GitForkRef'},
        'labels': {'key': 'labels', 'type': '[WebApiTagDefinition]'},
        'last_merge_commit': {'key': 'lastMergeCommit', 'type': 'GitCommitRef'},
        'last_merge_source_commit': {'key': 'lastMergeSourceCommit', 'type': 'GitCommitRef'},
        'last_merge_target_commit': {'key': 'lastMergeTargetCommit', 'type': 'GitCommitRef'},
        'merge_failure_message': {'key': 'mergeFailureMessage', 'type': 'str'},
        'merge_failure_type': {'key': 'mergeFailureType', 'type': 'object'},
        'merge_id': {'key': 'mergeId', 'type': 'str'},
        'merge_options': {'key': 'mergeOptions', 'type': 'GitPullRequestMergeOptions'},
        'merge_status': {'key': 'mergeStatus', 'type': 'object'},
        'pull_request_id': {'key': 'pullRequestId', 'type': 'int'},
        'remote_url': {'key': 'remoteUrl', 'type': 'str'},
        'repository': {'key': 'repository', 'type': 'GitRepository'},
        'reviewers': {'key': 'reviewers', 'type': '[IdentityRefWithVote]'},
        'source_ref_name': {'key': 'sourceRefName', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'},
        'supports_iterations': {'key': 'supportsIterations', 'type': 'bool'},
        'target_ref_name': {'key': 'targetRefName', 'type': 'str'},
        'title': {'key': 'title', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'work_item_refs': {'key': 'workItemRefs', 'type': '[ResourceRef]'}
    }

    def __init__(self, _links=None, artifact_id=None, auto_complete_set_by=None, closed_by=None, closed_date=None, code_review_id=None, commits=None, completion_options=None, completion_queue_time=None, created_by=None, creation_date=None, description=None, fork_source=None, labels=None, last_merge_commit=None, last_merge_source_commit=None, last_merge_target_commit=None, merge_failure_message=None, merge_failure_type=None, merge_id=None, merge_options=None, merge_status=None, pull_request_id=None, remote_url=None, repository=None, reviewers=None, source_ref_name=None, status=None, supports_iterations=None, target_ref_name=None, title=None, url=None, work_item_refs=None):
        super(GitPullRequest, self).__init__()
        self._links = _links
        self.artifact_id = artifact_id
        self.auto_complete_set_by = auto_complete_set_by
        self.closed_by = closed_by
        self.closed_date = closed_date
        self.code_review_id = code_review_id
        self.commits = commits
        self.completion_options = completion_options
        self.completion_queue_time = completion_queue_time
        self.created_by = created_by
        self.creation_date = creation_date
        self.description = description
        self.fork_source = fork_source
        self.labels = labels
        self.last_merge_commit = last_merge_commit
        self.last_merge_source_commit = last_merge_source_commit
        self.last_merge_target_commit = last_merge_target_commit
        self.merge_failure_message = merge_failure_message
        self.merge_failure_type = merge_failure_type
        self.merge_id = merge_id
        self.merge_options = merge_options
        self.merge_status = merge_status
        self.pull_request_id = pull_request_id
        self.remote_url = remote_url
        self.repository = repository
        self.reviewers = reviewers
        self.source_ref_name = source_ref_name
        self.status = status
        self.supports_iterations = supports_iterations
        self.target_ref_name = target_ref_name
        self.title = title
        self.url = url
        self.work_item_refs = work_item_refs
