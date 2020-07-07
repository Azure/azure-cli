# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WidgetPosition(Model):
    """WidgetPosition.

    :param column:
    :type column: int
    :param row:
    :type row: int
    """

    _attribute_map = {
        'column': {'key': 'column', 'type': 'int'},
        'row': {'key': 'row', 'type': 'int'}
    }

    def __init__(self, column=None, row=None):
        super(WidgetPosition, self).__init__()
        self.column = column
        self.row = row
