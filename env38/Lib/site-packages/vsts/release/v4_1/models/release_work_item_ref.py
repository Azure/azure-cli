# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseWorkItemRef(Model):
    """ReleaseWorkItemRef.

    :param assignee:
    :type assignee: str
    :param id:
    :type id: str
    :param state:
    :type state: str
    :param title:
    :type title: str
    :param type:
    :type type: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'assignee': {'key': 'assignee', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'state': {'key': 'state', 'type': 'str'},
        'title': {'key': 'title', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, assignee=None, id=None, state=None, title=None, type=None, url=None):
        super(ReleaseWorkItemRef, self).__init__()
        self.assignee = assignee
        self.id = id
        self.state = state
        self.title = title
        self.type = type
        self.url = url
