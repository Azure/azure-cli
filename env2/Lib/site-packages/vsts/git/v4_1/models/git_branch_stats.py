# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitBranchStats(Model):
    """GitBranchStats.

    :param ahead_count: Number of commits ahead.
    :type ahead_count: int
    :param behind_count: Number of commits behind.
    :type behind_count: int
    :param commit: Current commit.
    :type commit: :class:`GitCommitRef <git.v4_1.models.GitCommitRef>`
    :param is_base_version: True if this is the result for the base version.
    :type is_base_version: bool
    :param name: Name of the ref.
    :type name: str
    """

    _attribute_map = {
        'ahead_count': {'key': 'aheadCount', 'type': 'int'},
        'behind_count': {'key': 'behindCount', 'type': 'int'},
        'commit': {'key': 'commit', 'type': 'GitCommitRef'},
        'is_base_version': {'key': 'isBaseVersion', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, ahead_count=None, behind_count=None, commit=None, is_base_version=None, name=None):
        super(GitBranchStats, self).__init__()
        self.ahead_count = ahead_count
        self.behind_count = behind_count
        self.commit = commit
        self.is_base_version = is_base_version
        self.name = name
