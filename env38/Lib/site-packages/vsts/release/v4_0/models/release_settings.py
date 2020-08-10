# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseSettings(Model):
    """ReleaseSettings.

    :param retention_settings:
    :type retention_settings: :class:`RetentionSettings <release.v4_0.models.RetentionSettings>`
    """

    _attribute_map = {
        'retention_settings': {'key': 'retentionSettings', 'type': 'RetentionSettings'}
    }

    def __init__(self, retention_settings=None):
        super(ReleaseSettings, self).__init__()
        self.retention_settings = retention_settings
