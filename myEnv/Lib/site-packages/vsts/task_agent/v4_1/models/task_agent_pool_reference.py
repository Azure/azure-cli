# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentPoolReference(Model):
    """TaskAgentPoolReference.

    :param id:
    :type id: int
    :param is_hosted: Gets or sets a value indicating whether or not this pool is managed by the service.
    :type is_hosted: bool
    :param name:
    :type name: str
    :param pool_type: Gets or sets the type of the pool
    :type pool_type: object
    :param scope:
    :type scope: str
    :param size: Gets the current size of the pool.
    :type size: int
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'is_hosted': {'key': 'isHosted', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'pool_type': {'key': 'poolType', 'type': 'object'},
        'scope': {'key': 'scope', 'type': 'str'},
        'size': {'key': 'size', 'type': 'int'}
    }

    def __init__(self, id=None, is_hosted=None, name=None, pool_type=None, scope=None, size=None):
        super(TaskAgentPoolReference, self).__init__()
        self.id = id
        self.is_hosted = is_hosted
        self.name = name
        self.pool_type = pool_type
        self.scope = scope
        self.size = size
