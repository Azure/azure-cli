# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class ArmTemplate(Model):
    """An Azure Resource Manager template.

    :param display_name: The display name of the ARM template.
    :type display_name: str
    :param description: The description of the ARM template.
    :type description: str
    :param publisher: The publisher of the ARM template.
    :type publisher: str
    :param icon: The URI to the icon of the ARM template.
    :type icon: str
    :param contents: The contents of the ARM template.
    :type contents: object
    :param created_date: The creation date of the armTemplate.
    :type created_date: datetime
    :param parameters_value_files_info: File name and parameter values
     information from all azuredeploy.*.parameters.json for the ARM template.
    :type parameters_value_files_info: list of :class:`ParametersValueFileInfo
     <azure.mgmt.devtestlabs.models.ParametersValueFileInfo>`
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
        'display_name': {'key': 'properties.displayName', 'type': 'str'},
        'description': {'key': 'properties.description', 'type': 'str'},
        'publisher': {'key': 'properties.publisher', 'type': 'str'},
        'icon': {'key': 'properties.icon', 'type': 'str'},
        'contents': {'key': 'properties.contents', 'type': 'object'},
        'created_date': {'key': 'properties.createdDate', 'type': 'iso-8601'},
        'parameters_value_files_info': {'key': 'properties.parametersValueFilesInfo', 'type': '[ParametersValueFileInfo]'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'location': {'key': 'location', 'type': 'str'},
        'tags': {'key': 'tags', 'type': '{str}'},
    }

    def __init__(self, display_name=None, description=None, publisher=None, icon=None, contents=None, created_date=None, parameters_value_files_info=None, id=None, name=None, type=None, location=None, tags=None):
        self.display_name = display_name
        self.description = description
        self.publisher = publisher
        self.icon = icon
        self.contents = contents
        self.created_date = created_date
        self.parameters_value_files_info = parameters_value_files_info
        self.id = id
        self.name = name
        self.type = type
        self.location = location
        self.tags = tags
