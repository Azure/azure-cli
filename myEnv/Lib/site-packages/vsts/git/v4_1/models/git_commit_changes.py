# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitCommitChanges(Model):
    """GitCommitChanges.

    :param change_counts:
    :type change_counts: dict
    :param changes:
    :type changes: list of :class:`object <git.v4_1.models.object>`
    """

    _attribute_map = {
        'change_counts': {'key': 'changeCounts', 'type': '{int}'},
        'changes': {'key': 'changes', 'type': '[object]'}
    }

    def __init__(self, change_counts=None, changes=None):
        super(GitCommitChanges, self).__init__()
        self.change_counts = change_counts
        self.changes = changes
