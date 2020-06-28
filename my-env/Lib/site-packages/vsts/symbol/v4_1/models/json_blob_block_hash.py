# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class JsonBlobBlockHash(Model):
    """JsonBlobBlockHash.

    :param hash_bytes:
    :type hash_bytes: str
    """

    _attribute_map = {
        'hash_bytes': {'key': 'hashBytes', 'type': 'str'}
    }

    def __init__(self, hash_bytes=None):
        super(JsonBlobBlockHash, self).__init__()
        self.hash_bytes = hash_bytes
