# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class OverridableRunSettings(Model):
    """OverridableRunSettings.

    :param load_generator_machines_type:
    :type load_generator_machines_type: object
    :param static_agent_run_settings:
    :type static_agent_run_settings: :class:`StaticAgentRunSetting <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.StaticAgentRunSetting>`
    """

    _attribute_map = {
        'load_generator_machines_type': {'key': 'loadGeneratorMachinesType', 'type': 'object'},
        'static_agent_run_settings': {'key': 'staticAgentRunSettings', 'type': 'StaticAgentRunSetting'}
    }

    def __init__(self, load_generator_machines_type=None, static_agent_run_settings=None):
        super(OverridableRunSettings, self).__init__()
        self.load_generator_machines_type = load_generator_machines_type
        self.static_agent_run_settings = static_agent_run_settings
