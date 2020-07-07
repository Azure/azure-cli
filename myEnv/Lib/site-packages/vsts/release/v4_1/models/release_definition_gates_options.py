# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseDefinitionGatesOptions(Model):
    """ReleaseDefinitionGatesOptions.

    :param is_enabled:
    :type is_enabled: bool
    :param sampling_interval:
    :type sampling_interval: int
    :param stabilization_time:
    :type stabilization_time: int
    :param timeout:
    :type timeout: int
    """

    _attribute_map = {
        'is_enabled': {'key': 'isEnabled', 'type': 'bool'},
        'sampling_interval': {'key': 'samplingInterval', 'type': 'int'},
        'stabilization_time': {'key': 'stabilizationTime', 'type': 'int'},
        'timeout': {'key': 'timeout', 'type': 'int'}
    }

    def __init__(self, is_enabled=None, sampling_interval=None, stabilization_time=None, timeout=None):
        super(ReleaseDefinitionGatesOptions, self).__init__()
        self.is_enabled = is_enabled
        self.sampling_interval = sampling_interval
        self.stabilization_time = stabilization_time
        self.timeout = timeout
