# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class PercentageCostThresholdProperties(Model):
    """PercentageCostThresholdProperties.

    :param threshold_value: The cost threshold value.
    :type threshold_value: float
    """

    _attribute_map = {
        'threshold_value': {'key': 'thresholdValue', 'type': 'float'},
    }

    def __init__(self, threshold_value=None):
        self.threshold_value = threshold_value
