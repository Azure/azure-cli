# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemTypeBehavior(Model):
    """WorkItemTypeBehavior.

    :param behavior:
    :type behavior: :class:`WorkItemBehaviorReference <work-item-tracking.v4_0.models.WorkItemBehaviorReference>`
    :param is_default:
    :type is_default: bool
    :param url:
    :type url: str
    """

    _attribute_map = {
        'behavior': {'key': 'behavior', 'type': 'WorkItemBehaviorReference'},
        'is_default': {'key': 'isDefault', 'type': 'bool'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, behavior=None, is_default=None, url=None):
        super(WorkItemTypeBehavior, self).__init__()
        self.behavior = behavior
        self.is_default = is_default
        self.url = url
