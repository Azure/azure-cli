# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AssociatedWorkItem(Model):
    """AssociatedWorkItem.

    :param assigned_to:
    :type assigned_to: str
    :param id:
    :type id: int
    :param state:
    :type state: str
    :param title:
    :type title: str
    :param url: REST url
    :type url: str
    :param web_url:
    :type web_url: str
    :param work_item_type:
    :type work_item_type: str
    """

    _attribute_map = {
        'assigned_to': {'key': 'assignedTo', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'state': {'key': 'state', 'type': 'str'},
        'title': {'key': 'title', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'web_url': {'key': 'webUrl', 'type': 'str'},
        'work_item_type': {'key': 'workItemType', 'type': 'str'}
    }

    def __init__(self, assigned_to=None, id=None, state=None, title=None, url=None, web_url=None, work_item_type=None):
        super(AssociatedWorkItem, self).__init__()
        self.assigned_to = assigned_to
        self.id = id
        self.state = state
        self.title = title
        self.url = url
        self.web_url = web_url
        self.work_item_type = work_item_type
