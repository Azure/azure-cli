# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .deployment_group_reference import DeploymentGroupReference


class DeploymentGroup(DeploymentGroupReference):
    """DeploymentGroup.

    :param id:
    :type id: int
    :param name:
    :type name: str
    :param pool:
    :type pool: :class:`TaskAgentPoolReference <task-agent.v4_0.models.TaskAgentPoolReference>`
    :param project:
    :type project: :class:`ProjectReference <task-agent.v4_0.models.ProjectReference>`
    :param description:
    :type description: str
    :param machine_count:
    :type machine_count: int
    :param machines:
    :type machines: list of :class:`DeploymentMachine <task-agent.v4_0.models.DeploymentMachine>`
    :param machine_tags:
    :type machine_tags: list of str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'},
        'pool': {'key': 'pool', 'type': 'TaskAgentPoolReference'},
        'project': {'key': 'project', 'type': 'ProjectReference'},
        'description': {'key': 'description', 'type': 'str'},
        'machine_count': {'key': 'machineCount', 'type': 'int'},
        'machines': {'key': 'machines', 'type': '[DeploymentMachine]'},
        'machine_tags': {'key': 'machineTags', 'type': '[str]'}
    }

    def __init__(self, id=None, name=None, pool=None, project=None, description=None, machine_count=None, machines=None, machine_tags=None):
        super(DeploymentGroup, self).__init__(id=id, name=name, pool=pool, project=project)
        self.description = description
        self.machine_count = machine_count
        self.machines = machines
        self.machine_tags = machine_tags
