# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemRelationUpdates(Model):
    """WorkItemRelationUpdates.

    :param added:
    :type added: list of :class:`WorkItemRelation <work-item-tracking.v4_0.models.WorkItemRelation>`
    :param removed:
    :type removed: list of :class:`WorkItemRelation <work-item-tracking.v4_0.models.WorkItemRelation>`
    :param updated:
    :type updated: list of :class:`WorkItemRelation <work-item-tracking.v4_0.models.WorkItemRelation>`
    """

    _attribute_map = {
        'added': {'key': 'added', 'type': '[WorkItemRelation]'},
        'removed': {'key': 'removed', 'type': '[WorkItemRelation]'},
        'updated': {'key': 'updated', 'type': '[WorkItemRelation]'}
    }

    def __init__(self, added=None, removed=None, updated=None):
        super(WorkItemRelationUpdates, self).__init__()
        self.added = added
        self.removed = removed
        self.updated = updated
