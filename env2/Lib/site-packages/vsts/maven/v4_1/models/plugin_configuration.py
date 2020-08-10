# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PluginConfiguration(Model):
    """PluginConfiguration.

    :param goal_prefix:
    :type goal_prefix: str
    """

    _attribute_map = {
        'goal_prefix': {'key': 'goalPrefix', 'type': 'str'}
    }

    def __init__(self, goal_prefix=None):
        super(PluginConfiguration, self).__init__()
        self.goal_prefix = goal_prefix
