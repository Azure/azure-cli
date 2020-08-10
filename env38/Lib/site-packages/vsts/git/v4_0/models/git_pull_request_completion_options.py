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

    :param bypass_policy:
    :type bypass_policy: bool
    :param bypass_reason:
    :type bypass_reason: str
    :param delete_source_branch:
    :type delete_source_branch: bool
    :param merge_commit_message:
    :type merge_commit_message: str
    :param squash_merge:
    :type squash_merge: bool
    :param transition_work_items:
    :type transition_work_items: bool
    """

    _attribute_map = {
        'bypass_policy': {'key': 'bypassPolicy', 'type': 'bool'},
        'bypass_reason': {'key': 'bypassReason', 'type': 'str'},
        'delete_source_branch': {'key': 'deleteSourceBranch', 'type': 'bool'},
        'merge_commit_message': {'key': 'mergeCommitMessage', 'type': 'str'},
        'squash_merge': {'key': 'squashMerge', 'type': 'bool'},
        'transition_work_items': {'key': 'transitionWorkItems', 'type': 'bool'}
    }

    def __init__(self, bypass_policy=None, bypass_reason=None, delete_source_branch=None, merge_commit_message=None, squash_merge=None, transition_work_items=None):
        super(GitPullRequestCompletionOptions, self).__init__()
        self.bypass_policy = bypass_policy
        self.bypass_reason = bypass_reason
        self.delete_source_branch = delete_source_branch
        self.merge_commit_message = merge_commit_message
        self.squash_merge = squash_merge
        self.transition_work_items = transition_work_items
