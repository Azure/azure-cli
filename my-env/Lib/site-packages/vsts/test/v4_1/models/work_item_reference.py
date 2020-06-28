# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemReference(Model):
    """WorkItemReference.

    :param id:
    :type id: str
    :param name:
    :type name: str
    :param type:
    :type type: str
    :param url:
    :type url: str
    :param web_url:
    :type web_url: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'web_url': {'key': 'webUrl', 'type': 'str'}
    }

    def __init__(self, id=None, name=None, type=None, url=None, web_url=None):
        super(WorkItemReference, self).__init__()
        self.id = id
        self.name = name
        self.type = type
        self.url = url
        self.web_url = web_url
