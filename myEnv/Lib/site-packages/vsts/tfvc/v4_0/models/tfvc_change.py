# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .change import Change


class TfvcChange(Change):
    """TfvcChange.

    :param merge_sources: List of merge sources in case of rename or branch creation.
    :type merge_sources: list of :class:`TfvcMergeSource <tfvc.v4_0.models.TfvcMergeSource>`
    :param pending_version: Version at which a (shelved) change was pended against
    :type pending_version: int
    """

    _attribute_map = {
        'merge_sources': {'key': 'mergeSources', 'type': '[TfvcMergeSource]'},
        'pending_version': {'key': 'pendingVersion', 'type': 'int'}
    }

    def __init__(self, merge_sources=None, pending_version=None):
        super(TfvcChange, self).__init__()
        self.merge_sources = merge_sources
        self.pending_version = pending_version
