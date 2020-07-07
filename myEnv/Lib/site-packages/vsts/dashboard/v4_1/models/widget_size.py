# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WidgetSize(Model):
    """WidgetSize.

    :param column_span: The Width of the widget, expressed in dashboard grid columns.
    :type column_span: int
    :param row_span: The height of the widget, expressed in dashboard grid rows.
    :type row_span: int
    """

    _attribute_map = {
        'column_span': {'key': 'columnSpan', 'type': 'int'},
        'row_span': {'key': 'rowSpan', 'type': 'int'}
    }

    def __init__(self, column_span=None, row_span=None):
        super(WidgetSize, self).__init__()
        self.column_span = column_span
        self.row_span = row_span
