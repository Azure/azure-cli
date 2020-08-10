# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .task_agent_pool_reference import TaskAgentPoolReference


class TaskAgentPool(TaskAgentPoolReference):
    """TaskAgentPool.

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
    :param auto_provision: Gets or sets a value indicating whether or not a queue should be automatically provisioned for each project collection or not.
    :type auto_provision: bool
    :param created_by: Gets the identity who created this pool. The creator of the pool is automatically added into the administrators group for the pool on creation.
    :type created_by: :class:`IdentityRef <task-agent.v4_1.models.IdentityRef>`
    :param created_on: Gets the date/time of the pool creation.
    :type created_on: datetime
    :param owner: Gets the identity who owns or administrates this pool.
    :type owner: :class:`IdentityRef <task-agent.v4_1.models.IdentityRef>`
    :param properties:
    :type properties: :class:`object <task-agent.v4_1.models.object>`
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'is_hosted': {'key': 'isHosted', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'pool_type': {'key': 'poolType', 'type': 'object'},
        'scope': {'key': 'scope', 'type': 'str'},
        'size': {'key': 'size', 'type': 'int'},
        'auto_provision': {'key': 'autoProvision', 'type': 'bool'},
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'owner': {'key': 'owner', 'type': 'IdentityRef'},
        'properties': {'key': 'properties', 'type': 'object'}
    }

    def __init__(self, id=None, is_hosted=None, name=None, pool_type=None, scope=None, size=None, auto_provision=None, created_by=None, created_on=None, owner=None, properties=None):
        super(TaskAgentPool, self).__init__(id=id, is_hosted=is_hosted, name=name, pool_type=pool_type, scope=scope, size=size)
        self.auto_provision = auto_provision
        self.created_by = created_by
        self.created_on = created_on
        self.owner = owner
        self.properties = properties
