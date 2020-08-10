# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitPullRequestIterationChanges(Model):
    """GitPullRequestIterationChanges.

    :param change_entries:
    :type change_entries: list of :class:`GitPullRequestChange <git.v4_0.models.GitPullRequestChange>`
    :param next_skip:
    :type next_skip: int
    :param next_top:
    :type next_top: int
    """

    _attribute_map = {
        'change_entries': {'key': 'changeEntries', 'type': '[GitPullRequestChange]'},
        'next_skip': {'key': 'nextSkip', 'type': 'int'},
        'next_top': {'key': 'nextTop', 'type': 'int'}
    }

    def __init__(self, change_entries=None, next_skip=None, next_top=None):
        super(GitPullRequestIterationChanges, self).__init__()
        self.change_entries = change_entries
        self.next_skip = next_skip
        self.next_top = next_top
