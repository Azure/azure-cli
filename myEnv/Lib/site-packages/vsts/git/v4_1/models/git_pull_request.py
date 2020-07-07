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

    :param _links: Links to other related objects.
    :type _links: :class:`ReferenceLinks <git.v4_1.models.ReferenceLinks>`
    :param artifact_id: A string which uniquely identifies this pull request. To generate an artifact ID for a pull request, use this template: ```vstfs:///Git/PullRequestId/{projectId}/{repositoryId}/{pullRequestId}```
    :type artifact_id: str
    :param auto_complete_set_by: If set, auto-complete is enabled for this pull request and this is the identity that enabled it.
    :type auto_complete_set_by: :class:`IdentityRef <git.v4_1.models.IdentityRef>`
    :param closed_by: The user who closed the pull request.
    :type closed_by: :class:`IdentityRef <git.v4_1.models.IdentityRef>`
    :param closed_date: The date when the pull request was closed (completed, abandoned, or merged externally).
    :type closed_date: datetime
    :param code_review_id: The code review ID of the pull request. Used internally.
    :type code_review_id: int
    :param commits: The commits contained in the pull request.
    :type commits: list of :class:`GitCommitRef <git.v4_1.models.GitCommitRef>`
    :param completion_options: Options which affect how the pull request will be merged when it is completed.
    :type completion_options: :class:`GitPullRequestCompletionOptions <git.v4_1.models.GitPullRequestCompletionOptions>`
    :param completion_queue_time: The most recent date at which the pull request entered the queue to be completed. Used internally.
    :type completion_queue_time: datetime
    :param created_by: The identity of the user who created the pull request.
    :type created_by: :class:`IdentityRef <git.v4_1.models.IdentityRef>`
    :param creation_date: The date when the pull request was created.
    :type creation_date: datetime
    :param description: The description of the pull request.
    :type description: str
    :param fork_source: If this is a PR from a fork this will contain information about its source.
    :type fork_source: :class:`GitForkRef <git.v4_1.models.GitForkRef>`
    :param labels: The labels associated with the pull request.
    :type labels: list of :class:`WebApiTagDefinition <git.v4_1.models.WebApiTagDefinition>`
    :param last_merge_commit: The commit of the most recent pull request merge. If empty, the most recent merge is in progress or was unsuccessful.
    :type last_merge_commit: :class:`GitCommitRef <git.v4_1.models.GitCommitRef>`
    :param last_merge_source_commit: The commit at the head of the source branch at the time of the last pull request merge.
    :type last_merge_source_commit: :class:`GitCommitRef <git.v4_1.models.GitCommitRef>`
    :param last_merge_target_commit: The commit at the head of the target branch at the time of the last pull request merge.
    :type last_merge_target_commit: :class:`GitCommitRef <git.v4_1.models.GitCommitRef>`
    :param merge_failure_message: If set, pull request merge failed for this reason.
    :type merge_failure_message: str
    :param merge_failure_type: The type of failure (if any) of the pull request merge.
    :type merge_failure_type: object
    :param merge_id: The ID of the job used to run the pull request merge. Used internally.
    :type merge_id: str
    :param merge_options: Options used when the pull request merge runs. These are separate from completion options since completion happens only once and a new merge will run every time the source branch of the pull request changes.
    :type merge_options: :class:`GitPullRequestMergeOptions <git.v4_1.models.GitPullRequestMergeOptions>`
    :param merge_status: The current status of the pull request merge.
    :type merge_status: object
    :param pull_request_id: The ID of the pull request.
    :type pull_request_id: int
    :param remote_url: Used internally.
    :type remote_url: str
    :param repository: The repository containing the target branch of the pull request.
    :type repository: :class:`GitRepository <git.v4_1.models.GitRepository>`
    :param reviewers: A list of reviewers on the pull request along with the state of their votes.
    :type reviewers: list of :class:`IdentityRefWithVote <git.v4_1.models.IdentityRefWithVote>`
    :param source_ref_name: The name of the source branch of the pull request.
    :type source_ref_name: str
    :param status: The status of the pull request.
    :type status: object
    :param supports_iterations: If true, this pull request supports multiple iterations. Iteration support means individual pushes to the source branch of the pull request can be reviewed and comments left in one iteration will be tracked across future iterations.
    :type supports_iterations: bool
    :param target_ref_name: The name of the target branch of the pull request.
    :type target_ref_name: str
    :param title: The title of the pull request.
    :type title: str
    :param url: Used internally.
    :type url: str
    :param work_item_refs: Any work item references associated with this pull request.
    :type work_item_refs: list of :class:`ResourceRef <git.v4_1.models.ResourceRef>`
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
