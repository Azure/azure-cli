# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionAssignment(Model):
    """ExtensionAssignment.

    :param extension_gallery_id: Gets or sets the extension ID to assign.
    :type extension_gallery_id: str
    :param is_auto_assignment: Set to true if this a auto assignment scenario.
    :type is_auto_assignment: bool
    :param licensing_source: Gets or sets the licensing source.
    :type licensing_source: object
    :param user_ids: Gets or sets the user IDs to assign the extension to.
    :type user_ids: list of str
    """

    _attribute_map = {
        'extension_gallery_id': {'key': 'extensionGalleryId', 'type': 'str'},
        'is_auto_assignment': {'key': 'isAutoAssignment', 'type': 'bool'},
        'licensing_source': {'key': 'licensingSource', 'type': 'object'},
        'user_ids': {'key': 'userIds', 'type': '[str]'}
    }

    def __init__(self, extension_gallery_id=None, is_auto_assignment=None, licensing_source=None, user_ids=None):
        super(ExtensionAssignment, self).__init__()
        self.extension_gallery_id = extension_gallery_id
        self.is_auto_assignment = is_auto_assignment
        self.licensing_source = licensing_source
        self.user_ids = user_ids
