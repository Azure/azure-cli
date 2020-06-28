# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DeploymentGroupReference(Model):
    """DeploymentGroupReference.

    :param id: Deployment group identifier.
    :type id: int
    :param name: Name of the deployment group.
    :type name: str
    :param pool: Deployment pool in which deployment agents are registered.
    :type pool: :class:`TaskAgentPoolReference <task-agent.v4_1.models.TaskAgentPoolReference>`
    :param project: Project to which the deployment group belongs.
    :type project: :class:`ProjectReference <task-agent.v4_1.models.ProjectReference>`
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'},
        'pool': {'key': 'pool', 'type': 'TaskAgentPoolReference'},
        'project': {'key': 'project', 'type': 'ProjectReference'}
    }

    def __init__(self, id=None, name=None, pool=None, project=None):
        super(DeploymentGroupReference, self).__init__()
        self.id = id
        self.name = name
        self.pool = pool
        self.project = project
