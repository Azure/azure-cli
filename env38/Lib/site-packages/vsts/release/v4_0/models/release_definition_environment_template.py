# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseDefinitionEnvironmentTemplate(Model):
    """ReleaseDefinitionEnvironmentTemplate.

    :param can_delete:
    :type can_delete: bool
    :param category:
    :type category: str
    :param description:
    :type description: str
    :param environment:
    :type environment: :class:`ReleaseDefinitionEnvironment <release.v4_0.models.ReleaseDefinitionEnvironment>`
    :param icon_task_id:
    :type icon_task_id: str
    :param icon_uri:
    :type icon_uri: str
    :param id:
    :type id: str
    :param name:
    :type name: str
    """

    _attribute_map = {
        'can_delete': {'key': 'canDelete', 'type': 'bool'},
        'category': {'key': 'category', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'environment': {'key': 'environment', 'type': 'ReleaseDefinitionEnvironment'},
        'icon_task_id': {'key': 'iconTaskId', 'type': 'str'},
        'icon_uri': {'key': 'iconUri', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, can_delete=None, category=None, description=None, environment=None, icon_task_id=None, icon_uri=None, id=None, name=None):
        super(ReleaseDefinitionEnvironmentTemplate, self).__init__()
        self.can_delete = can_delete
        self.category = category
        self.description = description
        self.environment = environment
        self.icon_task_id = icon_task_id
        self.icon_uri = icon_uri
        self.id = id
        self.name = name
