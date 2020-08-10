# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskOrchestrationItem(Model):
    """TaskOrchestrationItem.

    :param item_type:
    :type item_type: object
    """

    _attribute_map = {
        'item_type': {'key': 'itemType', 'type': 'object'}
    }

    def __init__(self, item_type=None):
        super(TaskOrchestrationItem, self).__init__()
        self.item_type = item_type
