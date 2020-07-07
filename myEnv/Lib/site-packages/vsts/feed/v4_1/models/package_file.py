# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PackageFile(Model):
    """PackageFile.

    :param children:
    :type children: list of :class:`PackageFile <packaging.v4_1.models.PackageFile>`
    :param name:
    :type name: str
    :param protocol_metadata:
    :type protocol_metadata: :class:`ProtocolMetadata <packaging.v4_1.models.ProtocolMetadata>`
    """

    _attribute_map = {
        'children': {'key': 'children', 'type': '[PackageFile]'},
        'name': {'key': 'name', 'type': 'str'},
        'protocol_metadata': {'key': 'protocolMetadata', 'type': 'ProtocolMetadata'}
    }

    def __init__(self, children=None, name=None, protocol_metadata=None):
        super(PackageFile, self).__init__()
        self.children = children
        self.name = name
        self.protocol_metadata = protocol_metadata
