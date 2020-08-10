# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionVersion(Model):
    """ExtensionVersion.

    :param asset_uri:
    :type asset_uri: str
    :param badges:
    :type badges: list of :class:`ExtensionBadge <gallery.v4_0.models.ExtensionBadge>`
    :param fallback_asset_uri:
    :type fallback_asset_uri: str
    :param files:
    :type files: list of :class:`ExtensionFile <gallery.v4_0.models.ExtensionFile>`
    :param flags:
    :type flags: object
    :param last_updated:
    :type last_updated: datetime
    :param properties:
    :type properties: list of { key: str; value: str }
    :param validation_result_message:
    :type validation_result_message: str
    :param version:
    :type version: str
    :param version_description:
    :type version_description: str
    """

    _attribute_map = {
        'asset_uri': {'key': 'assetUri', 'type': 'str'},
        'badges': {'key': 'badges', 'type': '[ExtensionBadge]'},
        'fallback_asset_uri': {'key': 'fallbackAssetUri', 'type': 'str'},
        'files': {'key': 'files', 'type': '[ExtensionFile]'},
        'flags': {'key': 'flags', 'type': 'object'},
        'last_updated': {'key': 'lastUpdated', 'type': 'iso-8601'},
        'properties': {'key': 'properties', 'type': '[{ key: str; value: str }]'},
        'validation_result_message': {'key': 'validationResultMessage', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'},
        'version_description': {'key': 'versionDescription', 'type': 'str'}
    }

    def __init__(self, asset_uri=None, badges=None, fallback_asset_uri=None, files=None, flags=None, last_updated=None, properties=None, validation_result_message=None, version=None, version_description=None):
        super(ExtensionVersion, self).__init__()
        self.asset_uri = asset_uri
        self.badges = badges
        self.fallback_asset_uri = fallback_asset_uri
        self.files = files
        self.flags = flags
        self.last_updated = last_updated
        self.properties = properties
        self.validation_result_message = validation_result_message
        self.version = version
        self.version_description = version_description
