# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DebugEntryCreateBatch(Model):
    """DebugEntryCreateBatch.

    :param create_behavior: Defines what to do when a debug entry in the batch already exists.
    :type create_behavior: object
    :param debug_entries: The debug entries.
    :type debug_entries: list of :class:`DebugEntry <symbol.v4_1.models.DebugEntry>`
    """

    _attribute_map = {
        'create_behavior': {'key': 'createBehavior', 'type': 'object'},
        'debug_entries': {'key': 'debugEntries', 'type': '[DebugEntry]'}
    }

    def __init__(self, create_behavior=None, debug_entries=None):
        super(DebugEntryCreateBatch, self).__init__()
        self.create_behavior = create_behavior
        self.debug_entries = debug_entries
