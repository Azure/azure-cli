# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FieldUpdate(Model):
    """FieldUpdate.

    :param description:
    :type description: str
    :param id:
    :type id: str
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'}
    }

    def __init__(self, description=None, id=None):
        super(FieldUpdate, self).__init__()
        self.description = description
        self.id = id
