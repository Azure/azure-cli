# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskLogReference(Model):
    """TaskLogReference.

    :param id:
    :type id: int
    :param location:
    :type location: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'location': {'key': 'location', 'type': 'str'}
    }

    def __init__(self, id=None, location=None):
        super(TaskLogReference, self).__init__()
        self.id = id
        self.location = location
