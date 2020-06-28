# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemTypeUpdateModel(Model):
    """WorkItemTypeUpdateModel.

    :param color:
    :type color: str
    :param description:
    :type description: str
    :param icon:
    :type icon: str
    :param is_disabled:
    :type is_disabled: bool
    """

    _attribute_map = {
        'color': {'key': 'color', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'icon': {'key': 'icon', 'type': 'str'},
        'is_disabled': {'key': 'isDisabled', 'type': 'bool'}
    }

    def __init__(self, color=None, description=None, icon=None, is_disabled=None):
        super(WorkItemTypeUpdateModel, self).__init__()
        self.color = color
        self.description = description
        self.icon = icon
        self.is_disabled = is_disabled
