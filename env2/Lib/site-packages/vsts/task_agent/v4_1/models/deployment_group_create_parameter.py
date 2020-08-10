# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DeploymentGroupCreateParameter(Model):
    """DeploymentGroupCreateParameter.

    :param description: Description of the deployment group.
    :type description: str
    :param name: Name of the deployment group.
    :type name: str
    :param pool: Deployment pool in which deployment agents are registered. This is obsolete. Kept for compatibility. Will be marked obsolete explicitly by M132.
    :type pool: :class:`DeploymentGroupCreateParameterPoolProperty <task-agent.v4_1.models.DeploymentGroupCreateParameterPoolProperty>`
    :param pool_id: Identifier of the deployment pool in which deployment agents are registered.
    :type pool_id: int
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'pool': {'key': 'pool', 'type': 'DeploymentGroupCreateParameterPoolProperty'},
        'pool_id': {'key': 'poolId', 'type': 'int'}
    }

    def __init__(self, description=None, name=None, pool=None, pool_id=None):
        super(DeploymentGroupCreateParameter, self).__init__()
        self.description = description
        self.name = name
        self.pool = pool
        self.pool_id = pool_id
