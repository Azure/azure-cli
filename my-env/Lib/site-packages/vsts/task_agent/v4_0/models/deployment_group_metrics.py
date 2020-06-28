# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DeploymentGroupMetrics(Model):
    """DeploymentGroupMetrics.

    :param columns_header:
    :type columns_header: :class:`MetricsColumnsHeader <task-agent.v4_0.models.MetricsColumnsHeader>`
    :param deployment_group:
    :type deployment_group: :class:`DeploymentGroupReference <task-agent.v4_0.models.DeploymentGroupReference>`
    :param rows:
    :type rows: list of :class:`MetricsRow <task-agent.v4_0.models.MetricsRow>`
    """

    _attribute_map = {
        'columns_header': {'key': 'columnsHeader', 'type': 'MetricsColumnsHeader'},
        'deployment_group': {'key': 'deploymentGroup', 'type': 'DeploymentGroupReference'},
        'rows': {'key': 'rows', 'type': '[MetricsRow]'}
    }

    def __init__(self, columns_header=None, deployment_group=None, rows=None):
        super(DeploymentGroupMetrics, self).__init__()
        self.columns_header = columns_header
        self.deployment_group = deployment_group
        self.rows = rows
