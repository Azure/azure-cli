# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MetricsColumnsHeader(Model):
    """MetricsColumnsHeader.

    :param dimensions:
    :type dimensions: list of :class:`MetricsColumnMetaData <task-agent.v4_0.models.MetricsColumnMetaData>`
    :param metrics:
    :type metrics: list of :class:`MetricsColumnMetaData <task-agent.v4_0.models.MetricsColumnMetaData>`
    """

    _attribute_map = {
        'dimensions': {'key': 'dimensions', 'type': '[MetricsColumnMetaData]'},
        'metrics': {'key': 'metrics', 'type': '[MetricsColumnMetaData]'}
    }

    def __init__(self, dimensions=None, metrics=None):
        super(MetricsColumnsHeader, self).__init__()
        self.dimensions = dimensions
        self.metrics = metrics
