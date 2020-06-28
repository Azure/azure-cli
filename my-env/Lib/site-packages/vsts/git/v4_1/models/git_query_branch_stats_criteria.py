# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitQueryBranchStatsCriteria(Model):
    """GitQueryBranchStatsCriteria.

    :param base_commit:
    :type base_commit: :class:`GitVersionDescriptor <git.v4_1.models.GitVersionDescriptor>`
    :param target_commits:
    :type target_commits: list of :class:`GitVersionDescriptor <git.v4_1.models.GitVersionDescriptor>`
    """

    _attribute_map = {
        'base_commit': {'key': 'baseCommit', 'type': 'GitVersionDescriptor'},
        'target_commits': {'key': 'targetCommits', 'type': '[GitVersionDescriptor]'}
    }

    def __init__(self, base_commit=None, target_commits=None):
        super(GitQueryBranchStatsCriteria, self).__init__()
        self.base_commit = base_commit
        self.target_commits = target_commits
