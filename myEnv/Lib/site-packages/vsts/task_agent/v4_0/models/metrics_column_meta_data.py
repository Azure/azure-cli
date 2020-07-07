# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MetricsColumnMetaData(Model):
    """MetricsColumnMetaData.

    :param column_name:
    :type column_name: str
    :param column_value_type:
    :type column_value_type: str
    """

    _attribute_map = {
        'column_name': {'key': 'columnName', 'type': 'str'},
        'column_value_type': {'key': 'columnValueType', 'type': 'str'}
    }

    def __init__(self, column_name=None, column_value_type=None):
        super(MetricsColumnMetaData, self).__init__()
        self.column_name = column_name
        self.column_value_type = column_value_type
