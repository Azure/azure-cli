# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model

class NewOrganization(Model):
    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'data': {'key': 'data', 'type': 'str'},
    }

    def __init__(self, id=None, name=None, data=None):
        self.id = id
        self.name = name
        self.data = data