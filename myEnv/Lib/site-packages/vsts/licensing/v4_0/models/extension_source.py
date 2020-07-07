# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionSource(Model):
    """ExtensionSource.

    :param assignment_source: Assignment Source
    :type assignment_source: object
    :param extension_gallery_id: extension Identifier
    :type extension_gallery_id: str
    :param licensing_source: The licensing source of the extension. Account, Msdn, ect.
    :type licensing_source: object
    """

    _attribute_map = {
        'assignment_source': {'key': 'assignmentSource', 'type': 'object'},
        'extension_gallery_id': {'key': 'extensionGalleryId', 'type': 'str'},
        'licensing_source': {'key': 'licensingSource', 'type': 'object'}
    }

    def __init__(self, assignment_source=None, extension_gallery_id=None, licensing_source=None):
        super(ExtensionSource, self).__init__()
        self.assignment_source = assignment_source
        self.extension_gallery_id = extension_gallery_id
        self.licensing_source = licensing_source
