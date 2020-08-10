# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitCommitDiffs(Model):
    """GitCommitDiffs.

    :param ahead_count:
    :type ahead_count: int
    :param all_changes_included:
    :type all_changes_included: bool
    :param base_commit:
    :type base_commit: str
    :param behind_count:
    :type behind_count: int
    :param change_counts:
    :type change_counts: dict
    :param changes:
    :type changes: list of :class:`object <git.v4_1.models.object>`
    :param common_commit:
    :type common_commit: str
    :param target_commit:
    :type target_commit: str
    """

    _attribute_map = {
        'ahead_count': {'key': 'aheadCount', 'type': 'int'},
        'all_changes_included': {'key': 'allChangesIncluded', 'type': 'bool'},
        'base_commit': {'key': 'baseCommit', 'type': 'str'},
        'behind_count': {'key': 'behindCount', 'type': 'int'},
        'change_counts': {'key': 'changeCounts', 'type': '{int}'},
        'changes': {'key': 'changes', 'type': '[object]'},
        'common_commit': {'key': 'commonCommit', 'type': 'str'},
        'target_commit': {'key': 'targetCommit', 'type': 'str'}
    }

    def __init__(self, ahead_count=None, all_changes_included=None, base_commit=None, behind_count=None, change_counts=None, changes=None, common_commit=None, target_commit=None):
        super(GitCommitDiffs, self).__init__()
        self.ahead_count = ahead_count
        self.all_changes_included = all_changes_included
        self.base_commit = base_commit
        self.behind_count = behind_count
        self.change_counts = change_counts
        self.changes = changes
        self.common_commit = common_commit
        self.target_commit = target_commit
