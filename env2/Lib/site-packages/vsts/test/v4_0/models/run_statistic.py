# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class RunStatistic(Model):
    """RunStatistic.

    :param count:
    :type count: int
    :param outcome:
    :type outcome: str
    :param resolution_state:
    :type resolution_state: :class:`TestResolutionState <test.v4_0.models.TestResolutionState>`
    :param state:
    :type state: str
    """

    _attribute_map = {
        'count': {'key': 'count', 'type': 'int'},
        'outcome': {'key': 'outcome', 'type': 'str'},
        'resolution_state': {'key': 'resolutionState', 'type': 'TestResolutionState'},
        'state': {'key': 'state', 'type': 'str'}
    }

    def __init__(self, count=None, outcome=None, resolution_state=None, state=None):
        super(RunStatistic, self).__init__()
        self.count = count
        self.outcome = outcome
        self.resolution_state = resolution_state
        self.state = state
