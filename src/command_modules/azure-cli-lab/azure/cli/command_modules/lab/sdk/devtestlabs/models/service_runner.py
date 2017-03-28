# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class ServiceRunner(Model):
    """A container for a managed identity to execute DevTest lab services.

    :param identity: The identity of the resource.
    :type identity: :class:`IdentityProperties
     <azure.mgmt.devtestlabs.models.IdentityProperties>`
    :param id: The identifier of the resource.
    :type id: str
    :param name: The name of the resource.
    :type name: str
    :param type: The type of the resource.
    :type type: str
    :param location: The location of the resource.
    :type location: str
    :param tags: The tags of the resource.
    :type tags: dict
    """

    _attribute_map = {
        'identity': {'key': 'identity', 'type': 'IdentityProperties'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'location': {'key': 'location', 'type': 'str'},
        'tags': {'key': 'tags', 'type': '{str}'},
    }

    def __init__(self, identity=None, id=None, name=None, type=None, location=None, tags=None):
        self.identity = identity
        self.id = id
        self.name = name
        self.type = type
        self.location = location
        self.tags = tags
