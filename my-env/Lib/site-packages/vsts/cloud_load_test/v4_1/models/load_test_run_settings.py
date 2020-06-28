# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class LoadTestRunSettings(Model):
    """LoadTestRunSettings.

    :param agent_count:
    :type agent_count: int
    :param core_count:
    :type core_count: int
    :param cores_per_agent:
    :type cores_per_agent: int
    :param duration:
    :type duration: int
    :param load_generator_machines_type:
    :type load_generator_machines_type: object
    :param sampling_interval:
    :type sampling_interval: int
    :param warm_up_duration:
    :type warm_up_duration: int
    """

    _attribute_map = {
        'agent_count': {'key': 'agentCount', 'type': 'int'},
        'core_count': {'key': 'coreCount', 'type': 'int'},
        'cores_per_agent': {'key': 'coresPerAgent', 'type': 'int'},
        'duration': {'key': 'duration', 'type': 'int'},
        'load_generator_machines_type': {'key': 'loadGeneratorMachinesType', 'type': 'object'},
        'sampling_interval': {'key': 'samplingInterval', 'type': 'int'},
        'warm_up_duration': {'key': 'warmUpDuration', 'type': 'int'}
    }

    def __init__(self, agent_count=None, core_count=None, cores_per_agent=None, duration=None, load_generator_machines_type=None, sampling_interval=None, warm_up_duration=None):
        super(LoadTestRunSettings, self).__init__()
        self.agent_count = agent_count
        self.core_count = core_count
        self.cores_per_agent = cores_per_agent
        self.duration = duration
        self.load_generator_machines_type = load_generator_machines_type
        self.sampling_interval = sampling_interval
        self.warm_up_duration = warm_up_duration
