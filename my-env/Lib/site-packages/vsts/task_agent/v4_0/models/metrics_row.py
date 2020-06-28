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

    :param dimensions:
    :type dimensions: list of str
    :param metrics:
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
