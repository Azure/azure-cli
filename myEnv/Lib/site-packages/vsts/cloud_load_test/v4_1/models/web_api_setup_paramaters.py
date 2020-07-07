# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WebApiSetupParamaters(Model):
    """WebApiSetupParamaters.

    :param configurations:
    :type configurations: dict
    """

    _attribute_map = {
        'configurations': {'key': 'configurations', 'type': '{str}'}
    }

    def __init__(self, configurations=None):
        super(WebApiSetupParamaters, self).__init__()
        self.configurations = configurations
