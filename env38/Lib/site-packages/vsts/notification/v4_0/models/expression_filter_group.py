# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExpressionFilterGroup(Model):
    """ExpressionFilterGroup.

    :param end: The index of the last FilterClause in this group
    :type end: int
    :param level: Level of the group, since groups can be nested for each nested group the level will increase by 1
    :type level: int
    :param start: The index of the first FilterClause in this group
    :type start: int
    """

    _attribute_map = {
        'end': {'key': 'end', 'type': 'int'},
        'level': {'key': 'level', 'type': 'int'},
        'start': {'key': 'start', 'type': 'int'}
    }

    def __init__(self, end=None, level=None, start=None):
        super(ExpressionFilterGroup, self).__init__()
        self.end = end
        self.level = level
        self.start = start
