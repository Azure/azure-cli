# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DeploymentMachine(Model):
    """DeploymentMachine.

    :param agent: Deployment agent.
    :type agent: :class:`TaskAgent <task-agent.v4_1.models.TaskAgent>`
    :param id: Deployment target Identifier.
    :type id: int
    :param tags: Tags of the deployment target.
    :type tags: list of str
    """

    _attribute_map = {
        'agent': {'key': 'agent', 'type': 'TaskAgent'},
        'id': {'key': 'id', 'type': 'int'},
        'tags': {'key': 'tags', 'type': '[str]'}
    }

    def __init__(self, agent=None, id=None, tags=None):
        super(DeploymentMachine, self).__init__()
        self.agent = agent
        self.id = id
        self.tags = tags
