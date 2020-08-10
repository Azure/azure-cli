# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BoardFields(Model):
    """BoardFields.

    :param column_field:
    :type column_field: :class:`FieldReference <work.v4_0.models.FieldReference>`
    :param done_field:
    :type done_field: :class:`FieldReference <work.v4_0.models.FieldReference>`
    :param row_field:
    :type row_field: :class:`FieldReference <work.v4_0.models.FieldReference>`
    """

    _attribute_map = {
        'column_field': {'key': 'columnField', 'type': 'FieldReference'},
        'done_field': {'key': 'doneField', 'type': 'FieldReference'},
        'row_field': {'key': 'rowField', 'type': 'FieldReference'}
    }

    def __init__(self, column_field=None, done_field=None, row_field=None):
        super(BoardFields, self).__init__()
        self.column_field = column_field
        self.done_field = done_field
        self.row_field = row_field
