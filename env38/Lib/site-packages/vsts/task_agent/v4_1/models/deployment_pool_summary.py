# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DeploymentPoolSummary(Model):
    """DeploymentPoolSummary.

    :param deployment_groups: List of deployment groups referring to the deployment pool.
    :type deployment_groups: list of :class:`DeploymentGroupReference <task-agent.v4_1.models.DeploymentGroupReference>`
    :param offline_agents_count: Number of deployment agents that are offline.
    :type offline_agents_count: int
    :param online_agents_count: Number of deployment agents that are online.
    :type online_agents_count: int
    :param pool: Deployment pool.
    :type pool: :class:`TaskAgentPoolReference <task-agent.v4_1.models.TaskAgentPoolReference>`
    """

    _attribute_map = {
        'deployment_groups': {'key': 'deploymentGroups', 'type': '[DeploymentGroupReference]'},
        'offline_agents_count': {'key': 'offlineAgentsCount', 'type': 'int'},
        'online_agents_count': {'key': 'onlineAgentsCount', 'type': 'int'},
        'pool': {'key': 'pool', 'type': 'TaskAgentPoolReference'}
    }

    def __init__(self, deployment_groups=None, offline_agents_count=None, online_agents_count=None, pool=None):
        super(DeploymentPoolSummary, self).__init__()
        self.deployment_groups = deployment_groups
        self.offline_agents_count = offline_agents_count
        self.online_agents_count = online_agents_count
        self.pool = pool
