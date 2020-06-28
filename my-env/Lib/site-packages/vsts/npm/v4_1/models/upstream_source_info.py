# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class UpstreamSourceInfo(Model):
    """UpstreamSourceInfo.

    :param id:
    :type id: str
    :param location:
    :type location: str
    :param name:
    :type name: str
    :param source_type:
    :type source_type: object
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'location': {'key': 'location', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'source_type': {'key': 'sourceType', 'type': 'object'}
    }

    def __init__(self, id=None, location=None, name=None, source_type=None):
        super(UpstreamSourceInfo, self).__init__()
        self.id = id
        self.location = location
        self.name = name
        self.source_type = source_type
