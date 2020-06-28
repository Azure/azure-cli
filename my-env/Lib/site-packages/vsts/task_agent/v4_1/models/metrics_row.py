# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MetricsRow(Model):
    """MetricsRow.

    :param dimensions: The values of the properties mentioned as 'Dimensions' in column header. E.g. 1: For a property 'LastJobStatus' - metrics will be provided for 'passed', 'failed', etc. E.g. 2: For a property 'TargetState' - metrics will be provided for 'online', 'offline' targets.
    :type dimensions: list of str
    :param metrics: Metrics in serialized format. Should be deserialized based on the data type provided in header.
    :type metrics: list of str
    """

    _attribute_map = {
        'dimensions': {'key': 'dimensions', 'type': '[str]'},
        'metrics': {'key': 'metrics', 'type': '[str]'}
    }

    def __init__(self, dimensions=None, metrics=None):
        super(MetricsRow, self).__init__()
        self.dimensions = dimensions
        self.metrics = metrics
