# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemFieldUpdate(Model):
    """WorkItemFieldUpdate.

    :param new_value: The new value of the field.
    :type new_value: object
    :param old_value: The old value of the field.
    :type old_value: object
    """

    _attribute_map = {
        'new_value': {'key': 'newValue', 'type': 'object'},
        'old_value': {'key': 'oldValue', 'type': 'object'}
    }

    def __init__(self, new_value=None, old_value=None):
        super(WorkItemFieldUpdate, self).__init__()
        self.new_value = new_value
        self.old_value = old_value
