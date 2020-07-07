# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .deployment_machine_group_reference import DeploymentMachineGroupReference


class DeploymentMachineGroup(DeploymentMachineGroupReference):
    """DeploymentMachineGroup.

    :param id:
    :type id: int
    :param name:
    :type name: str
    :param pool:
    :type pool: :class:`TaskAgentPoolReference <task-agent.v4_1.models.TaskAgentPoolReference>`
    :param project:
    :type project: :class:`ProjectReference <task-agent.v4_1.models.ProjectReference>`
    :param machines:
    :type machines: list of :class:`DeploymentMachine <task-agent.v4_1.models.DeploymentMachine>`
    :param size:
    :type size: int
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'},
        'pool': {'key': 'pool', 'type': 'TaskAgentPoolReference'},
        'project': {'key': 'project', 'type': 'ProjectReference'},
        'machines': {'key': 'machines', 'type': '[DeploymentMachine]'},
        'size': {'key': 'size', 'type': 'int'}
    }

    def __init__(self, id=None, name=None, pool=None, project=None, machines=None, size=None):
        super(DeploymentMachineGroup, self).__init__(id=id, name=name, pool=pool, project=project)
        self.machines = machines
        self.size = size
