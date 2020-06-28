# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class InstalledExtensionQuery(Model):
    """InstalledExtensionQuery.

    :param asset_types:
    :type asset_types: list of str
    :param monikers:
    :type monikers: list of :class:`ExtensionIdentifier <extension-management.v4_0.models.ExtensionIdentifier>`
    """

    _attribute_map = {
        'asset_types': {'key': 'assetTypes', 'type': '[str]'},
        'monikers': {'key': 'monikers', 'type': '[ExtensionIdentifier]'}
    }

    def __init__(self, asset_types=None, monikers=None):
        super(InstalledExtensionQuery, self).__init__()
        self.asset_types = asset_types
        self.monikers = monikers
