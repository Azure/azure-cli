# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FavoriteItem(Model):
    """FavoriteItem.

    :param data: Application specific data for the entry
    :type data: str
    :param id: Unique Id of the the entry
    :type id: str
    :param name: Display text for favorite entry
    :type name: str
    :param type: Application specific favorite entry type. Empty or Null represents that Favorite item is a Folder
    :type type: str
    """

    _attribute_map = {
        'data': {'key': 'data', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, data=None, id=None, name=None, type=None):
        super(FavoriteItem, self).__init__()
        self.data = data
        self.id = id
        self.name = name
        self.type = type
