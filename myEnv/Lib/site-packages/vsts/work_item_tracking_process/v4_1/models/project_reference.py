# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProjectReference(Model):
    """ProjectReference.

    :param description: Description of the project
    :type description: str
    :param id: The ID of the project
    :type id: str
    :param name: Name of the project
    :type name: str
    :param url: Url of the project
    :type url: str
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, description=None, id=None, name=None, url=None):
        super(ProjectReference, self).__init__()
        self.description = description
        self.id = id
        self.name = name
        self.url = url
