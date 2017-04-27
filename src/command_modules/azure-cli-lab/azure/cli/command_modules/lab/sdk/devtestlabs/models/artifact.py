# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class Artifact(Model):
    """An artifact.

    :param title: The artifact's title.
    :type title: str
    :param description: The artifact's description.
    :type description: str
    :param publisher: The artifact's publisher.
    :type publisher: str
    :param file_path: The file path to the artifact.
    :type file_path: str
    :param icon: The URI to the artifact icon.
    :type icon: str
    :param target_os_type: The artifact's target OS.
    :type target_os_type: str
    :param parameters: The artifact's parameters.
    :type parameters: object
    :param created_date: The artifact's creation date.
    :type created_date: datetime
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
        'title': {'key': 'properties.title', 'type': 'str'},
        'description': {'key': 'properties.description', 'type': 'str'},
        'publisher': {'key': 'properties.publisher', 'type': 'str'},
        'file_path': {'key': 'properties.filePath', 'type': 'str'},
        'icon': {'key': 'properties.icon', 'type': 'str'},
        'target_os_type': {'key': 'properties.targetOsType', 'type': 'str'},
        'parameters': {'key': 'properties.parameters', 'type': 'object'},
        'created_date': {'key': 'properties.createdDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'location': {'key': 'location', 'type': 'str'},
        'tags': {'key': 'tags', 'type': '{str}'},
    }

    def __init__(self, title=None, description=None, publisher=None, file_path=None, icon=None, target_os_type=None, parameters=None, created_date=None, id=None, name=None, type=None, location=None, tags=None):
        self.title = title
        self.description = description
        self.publisher = publisher
        self.file_path = file_path
        self.icon = icon
        self.target_os_type = target_os_type
        self.parameters = parameters
        self.created_date = created_date
        self.id = id
        self.name = name
        self.type = type
        self.location = location
        self.tags = tags
