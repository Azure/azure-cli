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

    :param color: Color of the work item type
    :type color: str
    :param description: Description of the work item type
    :type description: str
    :param icon: Icon of the work item type
    :type icon: str
    :param is_disabled: Is the workitem type to be disabled
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
