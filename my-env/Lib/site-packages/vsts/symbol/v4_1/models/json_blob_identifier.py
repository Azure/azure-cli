# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class JsonBlobIdentifier(Model):
    """JsonBlobIdentifier.

    :param identifier_value:
    :type identifier_value: str
    """

    _attribute_map = {
        'identifier_value': {'key': 'identifierValue', 'type': 'str'}
    }

    def __init__(self, identifier_value=None):
        super(JsonBlobIdentifier, self).__init__()
        self.identifier_value = identifier_value
