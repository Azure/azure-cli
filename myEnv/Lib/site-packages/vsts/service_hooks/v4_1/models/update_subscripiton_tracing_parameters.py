# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class UpdateSubscripitonTracingParameters(Model):
    """UpdateSubscripitonTracingParameters.

    :param enabled:
    :type enabled: bool
    """

    _attribute_map = {
        'enabled': {'key': 'enabled', 'type': 'bool'}
    }

    def __init__(self, enabled=None):
        super(UpdateSubscripitonTracingParameters, self).__init__()
        self.enabled = enabled
