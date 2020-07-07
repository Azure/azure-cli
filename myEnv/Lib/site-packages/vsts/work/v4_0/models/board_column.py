# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BoardColumn(Model):
    """BoardColumn.

    :param column_type:
    :type column_type: object
    :param description:
    :type description: str
    :param id:
    :type id: str
    :param is_split:
    :type is_split: bool
    :param item_limit:
    :type item_limit: int
    :param name:
    :type name: str
    :param state_mappings:
    :type state_mappings: dict
    """

    _attribute_map = {
        'column_type': {'key': 'columnType', 'type': 'object'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'is_split': {'key': 'isSplit', 'type': 'bool'},
        'item_limit': {'key': 'itemLimit', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'},
        'state_mappings': {'key': 'stateMappings', 'type': '{str}'}
    }

    def __init__(self, column_type=None, description=None, id=None, is_split=None, item_limit=None, name=None, state_mappings=None):
        super(BoardColumn, self).__init__()
        self.column_type = column_type
        self.description = description
        self.id = id
        self.is_split = is_split
        self.item_limit = item_limit
        self.name = name
        self.state_mappings = state_mappings
