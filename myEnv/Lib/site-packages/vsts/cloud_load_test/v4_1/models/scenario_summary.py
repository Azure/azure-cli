# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ScenarioSummary(Model):
    """ScenarioSummary.

    :param max_user_load:
    :type max_user_load: int
    :param min_user_load:
    :type min_user_load: int
    :param scenario_name:
    :type scenario_name: str
    """

    _attribute_map = {
        'max_user_load': {'key': 'maxUserLoad', 'type': 'int'},
        'min_user_load': {'key': 'minUserLoad', 'type': 'int'},
        'scenario_name': {'key': 'scenarioName', 'type': 'str'}
    }

    def __init__(self, max_user_load=None, min_user_load=None, scenario_name=None):
        super(ScenarioSummary, self).__init__()
        self.max_user_load = max_user_load
        self.min_user_load = min_user_load
        self.scenario_name = scenario_name
