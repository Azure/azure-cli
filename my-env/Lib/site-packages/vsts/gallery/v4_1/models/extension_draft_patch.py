# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionDraftPatch(Model):
    """ExtensionDraftPatch.

    :param extension_data:
    :type extension_data: :class:`UnpackagedExtensionData <gallery.v4_1.models.UnpackagedExtensionData>`
    :param operation:
    :type operation: object
    """

    _attribute_map = {
        'extension_data': {'key': 'extensionData', 'type': 'UnpackagedExtensionData'},
        'operation': {'key': 'operation', 'type': 'object'}
    }

    def __init__(self, extension_data=None, operation=None):
        super(ExtensionDraftPatch, self).__init__()
        self.extension_data = extension_data
        self.operation = operation
