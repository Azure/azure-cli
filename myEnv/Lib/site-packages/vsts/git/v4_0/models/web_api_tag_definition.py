# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WebApiTagDefinition(Model):
    """WebApiTagDefinition.

    :param active:
    :type active: bool
    :param id:
    :type id: str
    :param name:
    :type name: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'active': {'key': 'active', 'type': 'bool'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, active=None, id=None, name=None, url=None):
        super(WebApiTagDefinition, self).__init__()
        self.active = active
        self.id = id
        self.name = name
        self.url = url
