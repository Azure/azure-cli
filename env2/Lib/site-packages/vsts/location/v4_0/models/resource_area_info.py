# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ResourceAreaInfo(Model):
    """ResourceAreaInfo.

    :param id:
    :type id: str
    :param location_url:
    :type location_url: str
    :param name:
    :type name: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'location_url': {'key': 'locationUrl', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, id=None, location_url=None, name=None):
        super(ResourceAreaInfo, self).__init__()
        self.id = id
        self.location_url = location_url
        self.name = name
