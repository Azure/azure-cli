# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FeatureFlagPatch(Model):
    """FeatureFlagPatch.

    :param state:
    :type state: str
    """

    _attribute_map = {
        'state': {'key': 'state', 'type': 'str'}
    }

    def __init__(self, state=None):
        super(FeatureFlagPatch, self).__init__()
        self.state = state
