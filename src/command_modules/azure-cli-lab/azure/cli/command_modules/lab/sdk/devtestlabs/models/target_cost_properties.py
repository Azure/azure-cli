# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class TargetCostProperties(Model):
    """TargetCostProperties.

    :param status: Target cost status. Possible values include: 'Enabled',
     'Disabled'
    :type status: str or :class:`TargetCostStatus
     <azure.mgmt.devtestlabs.models.TargetCostStatus>`
    :param target: Lab target cost
    :type target: int
    :param cost_thresholds: Cost thresholds.
    :type cost_thresholds: list of :class:`CostThresholdProperties
     <azure.mgmt.devtestlabs.models.CostThresholdProperties>`
    :param cycle_start_date_time: Reporting cycle start date.
    :type cycle_start_date_time: str
    :param cycle_end_date_time: Reporting cycle end date.
    :type cycle_end_date_time: str
    :param cycle_type: Reporting cycle type. Possible values include:
     'CalendarMonth', 'Custom'
    :type cycle_type: str or :class:`ReportingCycleType
     <azure.mgmt.devtestlabs.models.ReportingCycleType>`
    """

    _attribute_map = {
        'status': {'key': 'status', 'type': 'str'},
        'target': {'key': 'target', 'type': 'int'},
        'cost_thresholds': {'key': 'costThresholds', 'type': '[CostThresholdProperties]'},
        'cycle_start_date_time': {'key': 'cycleStartDateTime', 'type': 'str'},
        'cycle_end_date_time': {'key': 'cycleEndDateTime', 'type': 'str'},
        'cycle_type': {'key': 'cycleType', 'type': 'str'},
    }

    def __init__(self, status=None, target=None, cost_thresholds=None, cycle_start_date_time=None, cycle_end_date_time=None, cycle_type=None):
        self.status = status
        self.target = target
        self.cost_thresholds = cost_thresholds
        self.cycle_start_date_time = cycle_start_date_time
        self.cycle_end_date_time = cycle_end_date_time
        self.cycle_type = cycle_type
