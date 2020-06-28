# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MetadataItem(Model):
    """MetadataItem.

    :param count: The count of the metadata item
    :type count: int
    :param name: The name of the metadata item
    :type name: str
    """

    _attribute_map = {
        'count': {'key': 'count', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, count=None, name=None):
        super(MetadataItem, self).__init__()
        self.count = count
        self.name = name
