# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SummaryPercentileData(Model):
    """SummaryPercentileData.

    :param percentile:
    :type percentile: int
    :param percentile_value:
    :type percentile_value: float
    """

    _attribute_map = {
        'percentile': {'key': 'percentile', 'type': 'int'},
        'percentile_value': {'key': 'percentileValue', 'type': 'float'}
    }

    def __init__(self, percentile=None, percentile_value=None):
        super(SummaryPercentileData, self).__init__()
        self.percentile = percentile
        self.percentile_value = percentile_value
