# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BacklogColumn(Model):
    """BacklogColumn.

    :param column_field_reference:
    :type column_field_reference: :class:`WorkItemFieldReference <work.v4_1.models.WorkItemFieldReference>`
    :param width:
    :type width: int
    """

    _attribute_map = {
        'column_field_reference': {'key': 'columnFieldReference', 'type': 'WorkItemFieldReference'},
        'width': {'key': 'width', 'type': 'int'}
    }

    def __init__(self, column_field_reference=None, width=None):
        super(BacklogColumn, self).__init__()
        self.column_field_reference = column_field_reference
        self.width = width
