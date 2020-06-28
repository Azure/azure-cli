# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionPayload(Model):
    """ExtensionPayload.

    :param description:
    :type description: str
    :param display_name:
    :type display_name: str
    :param file_name:
    :type file_name: str
    :param installation_targets:
    :type installation_targets: list of :class:`InstallationTarget <gallery.v4_1.models.InstallationTarget>`
    :param is_signed_by_microsoft:
    :type is_signed_by_microsoft: bool
    :param is_valid:
    :type is_valid: bool
    :param metadata:
    :type metadata: list of { key: str; value: str }
    :param type:
    :type type: object
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'file_name': {'key': 'fileName', 'type': 'str'},
        'installation_targets': {'key': 'installationTargets', 'type': '[InstallationTarget]'},
        'is_signed_by_microsoft': {'key': 'isSignedByMicrosoft', 'type': 'bool'},
        'is_valid': {'key': 'isValid', 'type': 'bool'},
        'metadata': {'key': 'metadata', 'type': '[{ key: str; value: str }]'},
        'type': {'key': 'type', 'type': 'object'}
    }

    def __init__(self, description=None, display_name=None, file_name=None, installation_targets=None, is_signed_by_microsoft=None, is_valid=None, metadata=None, type=None):
        super(ExtensionPayload, self).__init__()
        self.description = description
        self.display_name = display_name
        self.file_name = file_name
        self.installation_targets = installation_targets
        self.is_signed_by_microsoft = is_signed_by_microsoft
        self.is_valid = is_valid
        self.metadata = metadata
        self.type = type
