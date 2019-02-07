# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PoolDetailsDepth(Model):
    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'scope': {'key': 'scope', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'isHosted': {'key': 'isHosted', 'type': 'str'},
        'poolType': {'key': 'poolType', 'type': 'str'},
        'size': {'key': 'size', 'type': 'str'},
    }

    def __init__(self, id=None, scope=None, name=None, isHosted=None, poolType=None, size=None):  # pylint: disable=super-init-not-called,redefined-builtin
        self.id = id
        self.scope = scope
        self.name = name
        self.isHosted = isHosted
        self.poolType = poolType
        self.size = size
