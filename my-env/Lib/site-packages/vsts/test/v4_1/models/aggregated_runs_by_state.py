# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AggregatedRunsByState(Model):
    """AggregatedRunsByState.

    :param runs_count:
    :type runs_count: int
    :param state:
    :type state: object
    """

    _attribute_map = {
        'runs_count': {'key': 'runsCount', 'type': 'int'},
        'state': {'key': 'state', 'type': 'object'}
    }

    def __init__(self, runs_count=None, state=None):
        super(AggregatedRunsByState, self).__init__()
        self.runs_count = runs_count
        self.state = state
