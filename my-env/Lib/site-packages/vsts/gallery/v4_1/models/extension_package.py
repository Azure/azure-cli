# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionPackage(Model):
    """ExtensionPackage.

    :param extension_manifest: Base 64 encoded extension package
    :type extension_manifest: str
    """

    _attribute_map = {
        'extension_manifest': {'key': 'extensionManifest', 'type': 'str'}
    }

    def __init__(self, extension_manifest=None):
        super(ExtensionPackage, self).__init__()
        self.extension_manifest = extension_manifest
