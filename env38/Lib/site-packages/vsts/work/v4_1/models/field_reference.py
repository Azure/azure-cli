# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FieldReference(Model):
    """FieldReference.

    :param reference_name: fieldRefName for the field
    :type reference_name: str
    :param url: Full http link to more information about the field
    :type url: str
    """

    _attribute_map = {
        'reference_name': {'key': 'referenceName', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, reference_name=None, url=None):
        super(FieldReference, self).__init__()
        self.reference_name = reference_name
        self.url = url
