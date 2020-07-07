# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ResourceContainer(Model):
    """ResourceContainer.

    :param base_url: Gets or sets the container's base URL, i.e. the URL of the host (collection, application, or deploument) containing the container resource.
    :type base_url: str
    :param id: Gets or sets the container's specific Id.
    :type id: str
    :param name: Gets or sets the container's name.
    :type name: str
    :param url: Gets or sets the container's REST API URL.
    :type url: str
    """

    _attribute_map = {
        'base_url': {'key': 'baseUrl', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, base_url=None, id=None, name=None, url=None):
        super(ResourceContainer, self).__init__()
        self.base_url = base_url
        self.id = id
        self.name = name
        self.url = url
