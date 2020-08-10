# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class IdentityUpdateData(Model):
    """IdentityUpdateData.

    :param id:
    :type id: str
    :param index:
    :type index: int
    :param updated:
    :type updated: bool
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'index': {'key': 'index', 'type': 'int'},
        'updated': {'key': 'updated', 'type': 'bool'}
    }

    def __init__(self, id=None, index=None, updated=None):
        super(IdentityUpdateData, self).__init__()
        self.id = id
        self.index = index
        self.updated = updated
