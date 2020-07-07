# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestRunCounterInstance(Model):
    """TestRunCounterInstance.

    :param category_name:
    :type category_name: str
    :param counter_instance_id:
    :type counter_instance_id: str
    :param counter_name:
    :type counter_name: str
    :param counter_units:
    :type counter_units: str
    :param instance_name:
    :type instance_name: str
    :param is_preselected_counter:
    :type is_preselected_counter: bool
    :param machine_name:
    :type machine_name: str
    :param part_of_counter_groups:
    :type part_of_counter_groups: list of str
    :param summary_data:
    :type summary_data: :class:`WebInstanceSummaryData <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.WebInstanceSummaryData>`
    :param unique_name:
    :type unique_name: str
    """

    _attribute_map = {
        'category_name': {'key': 'categoryName', 'type': 'str'},
        'counter_instance_id': {'key': 'counterInstanceId', 'type': 'str'},
        'counter_name': {'key': 'counterName', 'type': 'str'},
        'counter_units': {'key': 'counterUnits', 'type': 'str'},
        'instance_name': {'key': 'instanceName', 'type': 'str'},
        'is_preselected_counter': {'key': 'isPreselectedCounter', 'type': 'bool'},
        'machine_name': {'key': 'machineName', 'type': 'str'},
        'part_of_counter_groups': {'key': 'partOfCounterGroups', 'type': '[str]'},
        'summary_data': {'key': 'summaryData', 'type': 'WebInstanceSummaryData'},
        'unique_name': {'key': 'uniqueName', 'type': 'str'}
    }

    def __init__(self, category_name=None, counter_instance_id=None, counter_name=None, counter_units=None, instance_name=None, is_preselected_counter=None, machine_name=None, part_of_counter_groups=None, summary_data=None, unique_name=None):
        super(TestRunCounterInstance, self).__init__()
        self.category_name = category_name
        self.counter_instance_id = counter_instance_id
        self.counter_name = counter_name
        self.counter_units = counter_units
        self.instance_name = instance_name
        self.is_preselected_counter = is_preselected_counter
        self.machine_name = machine_name
        self.part_of_counter_groups = part_of_counter_groups
        self.summary_data = summary_data
        self.unique_name = unique_name
