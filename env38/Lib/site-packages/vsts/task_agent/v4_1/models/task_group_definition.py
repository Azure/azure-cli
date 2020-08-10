# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskGroupDefinition(Model):
    """TaskGroupDefinition.

    :param display_name:
    :type display_name: str
    :param is_expanded:
    :type is_expanded: bool
    :param name:
    :type name: str
    :param tags:
    :type tags: list of str
    :param visible_rule:
    :type visible_rule: str
    """

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'is_expanded': {'key': 'isExpanded', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'tags': {'key': 'tags', 'type': '[str]'},
        'visible_rule': {'key': 'visibleRule', 'type': 'str'}
    }

    def __init__(self, display_name=None, is_expanded=None, name=None, tags=None, visible_rule=None):
        super(TaskGroupDefinition, self).__init__()
        self.display_name = display_name
        self.is_expanded = is_expanded
        self.name = name
        self.tags = tags
        self.visible_rule = visible_rule
