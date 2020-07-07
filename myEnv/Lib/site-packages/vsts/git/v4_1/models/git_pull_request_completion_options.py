# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitPullRequestCompletionOptions(Model):
    """GitPullRequestCompletionOptions.

    :param bypass_policy: If true, policies will be explicitly bypassed while the pull request is completed.
    :type bypass_policy: bool
    :param bypass_reason: If policies are bypassed, this reason is stored as to why bypass was used.
    :type bypass_reason: str
    :param delete_source_branch: If true, the source branch of the pull request will be deleted after completion.
    :type delete_source_branch: bool
    :param merge_commit_message: If set, this will be used as the commit message of the merge commit.
    :type merge_commit_message: str
    :param squash_merge: If true, the commits in the pull request will be squash-merged into the specified target branch on completion.
    :type squash_merge: bool
    :param transition_work_items: If true, we will attempt to transition any work items linked to the pull request into the next logical state (i.e. Active -> Resolved)
    :type transition_work_items: bool
    :param triggered_by_auto_complete: If true, the current completion attempt was triggered via auto-complete. Used internally.
    :type triggered_by_auto_complete: bool
    """

    _attribute_map = {
        'bypass_policy': {'key': 'bypassPolicy', 'type': 'bool'},
        'bypass_reason': {'key': 'bypassReason', 'type': 'str'},
        'delete_source_branch': {'key': 'deleteSourceBranch', 'type': 'bool'},
        'merge_commit_message': {'key': 'mergeCommitMessage', 'type': 'str'},
        'squash_merge': {'key': 'squashMerge', 'type': 'bool'},
        'transition_work_items': {'key': 'transitionWorkItems', 'type': 'bool'},
        'triggered_by_auto_complete': {'key': 'triggeredByAutoComplete', 'type': 'bool'}
    }

    def __init__(self, bypass_policy=None, bypass_reason=None, delete_source_branch=None, merge_commit_message=None, squash_merge=None, transition_work_items=None, triggered_by_auto_complete=None):
        super(GitPullRequestCompletionOptions, self).__init__()
        self.bypass_policy = bypass_policy
        self.bypass_reason = bypass_reason
        self.delete_source_branch = delete_source_branch
        self.merge_commit_message = merge_commit_message
        self.squash_merge = squash_merge
        self.transition_work_items = transition_work_items
        self.triggered_by_auto_complete = triggered_by_auto_complete
