# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProtocolMetadata(Model):
    """ProtocolMetadata.

    :param data:
    :type data: object
    :param schema_version:
    :type schema_version: int
    """

    _attribute_map = {
        'data': {'key': 'data', 'type': 'object'},
        'schema_version': {'key': 'schemaVersion', 'type': 'int'}
    }

    def __init__(self, data=None, schema_version=None):
        super(ProtocolMetadata, self).__init__()
        self.data = data
        self.schema_version = schema_version
