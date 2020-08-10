# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BoardUserSettings(Model):
    """BoardUserSettings.

    :param auto_refresh_state:
    :type auto_refresh_state: bool
    """

    _attribute_map = {
        'auto_refresh_state': {'key': 'autoRefreshState', 'type': 'bool'}
    }

    def __init__(self, auto_refresh_state=None):
        super(BoardUserSettings, self).__init__()
        self.auto_refresh_state = auto_refresh_state
