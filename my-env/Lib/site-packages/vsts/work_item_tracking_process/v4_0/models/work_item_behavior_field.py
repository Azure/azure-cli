# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemBehaviorField(Model):
    """WorkItemBehaviorField.

    :param behavior_field_id:
    :type behavior_field_id: str
    :param id:
    :type id: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'behavior_field_id': {'key': 'behaviorFieldId', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, behavior_field_id=None, id=None, url=None):
        super(WorkItemBehaviorField, self).__init__()
        self.behavior_field_id = behavior_field_id
        self.id = id
        self.url = url
