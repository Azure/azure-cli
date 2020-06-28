# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class LoadTestDefinition(Model):
    """LoadTestDefinition.

    :param agent_count:
    :type agent_count: int
    :param browser_mixs:
    :type browser_mixs: list of :class:`BrowserMix <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.BrowserMix>`
    :param core_count:
    :type core_count: int
    :param cores_per_agent:
    :type cores_per_agent: int
    :param load_generation_geo_locations:
    :type load_generation_geo_locations: list of :class:`LoadGenerationGeoLocation <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.LoadGenerationGeoLocation>`
    :param load_pattern_name:
    :type load_pattern_name: str
    :param load_test_name:
    :type load_test_name: str
    :param max_vusers:
    :type max_vusers: int
    :param run_duration:
    :type run_duration: int
    :param sampling_rate:
    :type sampling_rate: int
    :param think_time:
    :type think_time: int
    :param urls:
    :type urls: list of str
    """

    _attribute_map = {
        'agent_count': {'key': 'agentCount', 'type': 'int'},
        'browser_mixs': {'key': 'browserMixs', 'type': '[BrowserMix]'},
        'core_count': {'key': 'coreCount', 'type': 'int'},
        'cores_per_agent': {'key': 'coresPerAgent', 'type': 'int'},
        'load_generation_geo_locations': {'key': 'loadGenerationGeoLocations', 'type': '[LoadGenerationGeoLocation]'},
        'load_pattern_name': {'key': 'loadPatternName', 'type': 'str'},
        'load_test_name': {'key': 'loadTestName', 'type': 'str'},
        'max_vusers': {'key': 'maxVusers', 'type': 'int'},
        'run_duration': {'key': 'runDuration', 'type': 'int'},
        'sampling_rate': {'key': 'samplingRate', 'type': 'int'},
        'think_time': {'key': 'thinkTime', 'type': 'int'},
        'urls': {'key': 'urls', 'type': '[str]'}
    }

    def __init__(self, agent_count=None, browser_mixs=None, core_count=None, cores_per_agent=None, load_generation_geo_locations=None, load_pattern_name=None, load_test_name=None, max_vusers=None, run_duration=None, sampling_rate=None, think_time=None, urls=None):
        super(LoadTestDefinition, self).__init__()
        self.agent_count = agent_count
        self.browser_mixs = browser_mixs
        self.core_count = core_count
        self.cores_per_agent = cores_per_agent
        self.load_generation_geo_locations = load_generation_geo_locations
        self.load_pattern_name = load_pattern_name
        self.load_test_name = load_test_name
        self.max_vusers = max_vusers
        self.run_duration = run_duration
        self.sampling_rate = sampling_rate
        self.think_time = think_time
        self.urls = urls
