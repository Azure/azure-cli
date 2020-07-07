# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class JsonBlobIdentifierWithBlocks(Model):
    """JsonBlobIdentifierWithBlocks.

    :param block_hashes:
    :type block_hashes: list of :class:`JsonBlobBlockHash <symbol.v4_1.models.JsonBlobBlockHash>`
    :param identifier_value:
    :type identifier_value: str
    """

    _attribute_map = {
        'block_hashes': {'key': 'blockHashes', 'type': '[JsonBlobBlockHash]'},
        'identifier_value': {'key': 'identifierValue', 'type': 'str'}
    }

    def __init__(self, block_hashes=None, identifier_value=None):
        super(JsonBlobIdentifierWithBlocks, self).__init__()
        self.block_hashes = block_hashes
        self.identifier_value = identifier_value
