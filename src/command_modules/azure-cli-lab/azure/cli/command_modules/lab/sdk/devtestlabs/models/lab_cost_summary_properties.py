# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class LabCostSummaryProperties(Model):
    """LabCostSummaryProperties.

    :param estimated_lab_cost: The cost component of the cost item.
    :type estimated_lab_cost: float
    """

    _attribute_map = {
        'estimated_lab_cost': {'key': 'estimatedLabCost', 'type': 'float'},
    }

    def __init__(self, estimated_lab_cost=None):
        self.estimated_lab_cost = estimated_lab_cost
