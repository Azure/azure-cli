# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionFile(Model):
    """ExtensionFile.

    :param asset_type:
    :type asset_type: str
    :param language:
    :type language: str
    :param source:
    :type source: str
    """

    _attribute_map = {
        'asset_type': {'key': 'assetType', 'type': 'str'},
        'language': {'key': 'language', 'type': 'str'},
        'source': {'key': 'source', 'type': 'str'}
    }

    def __init__(self, asset_type=None, language=None, source=None):
        super(ExtensionFile, self).__init__()
        self.asset_type = asset_type
        self.language = language
        self.source = source
