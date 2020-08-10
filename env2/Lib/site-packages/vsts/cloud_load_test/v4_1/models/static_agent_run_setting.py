# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class StaticAgentRunSetting(Model):
    """StaticAgentRunSetting.

    :param load_generator_machines_type:
    :type load_generator_machines_type: object
    :param static_agent_group_name:
    :type static_agent_group_name: str
    """

    _attribute_map = {
        'load_generator_machines_type': {'key': 'loadGeneratorMachinesType', 'type': 'object'},
        'static_agent_group_name': {'key': 'staticAgentGroupName', 'type': 'str'}
    }

    def __init__(self, load_generator_machines_type=None, static_agent_group_name=None):
        super(StaticAgentRunSetting, self).__init__()
        self.load_generator_machines_type = load_generator_machines_type
        self.static_agent_group_name = static_agent_group_name
