# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemQuerySortColumn(Model):
    """WorkItemQuerySortColumn.

    :param descending:
    :type descending: bool
    :param field:
    :type field: :class:`WorkItemFieldReference <work-item-tracking.v4_0.models.WorkItemFieldReference>`
    """

    _attribute_map = {
        'descending': {'key': 'descending', 'type': 'bool'},
        'field': {'key': 'field', 'type': 'WorkItemFieldReference'}
    }

    def __init__(self, descending=None, field=None):
        super(WorkItemQuerySortColumn, self).__init__()
        self.descending = descending
        self.field = field
