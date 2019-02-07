# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PoolDetails(Model):
    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'projectId': {'key': 'projectId', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'pool': {'key': 'subscriptionId', 'type': 'PoolDetailsDepth'}
    }

    def __init__(self, id=None, projectId=None, name=None, pool=None):  # pylint: disable=super-init-not-called,redefined-builtin
        self.id = id
        self.projectId = projectId
        self.name = name
        self.pool = pool
