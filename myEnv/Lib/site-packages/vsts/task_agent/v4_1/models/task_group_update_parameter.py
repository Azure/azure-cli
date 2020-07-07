# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskGroupUpdateParameter(Model):
    """TaskGroupUpdateParameter.

    :param author: Sets author name of the task group.
    :type author: str
    :param category: Sets category of the task group.
    :type category: str
    :param comment: Sets comment of the task group.
    :type comment: str
    :param description: Sets description of the task group.
    :type description: str
    :param friendly_name: Sets friendly name of the task group.
    :type friendly_name: str
    :param icon_url: Sets url icon of the task group.
    :type icon_url: str
    :param id: Sets the unique identifier of this field.
    :type id: str
    :param inputs: Sets input for the task group.
    :type inputs: list of :class:`TaskInputDefinition <task-agent.v4_1.models.TaskInputDefinition>`
    :param instance_name_format: Sets display name of the task group.
    :type instance_name_format: str
    :param name: Sets name of the task group.
    :type name: str
    :param parent_definition_id: Gets or sets parent task group Id. This is used while creating a draft task group.
    :type parent_definition_id: str
    :param revision: Sets revision of the task group.
    :type revision: int
    :param runs_on: Sets RunsOn of the task group. Value can be 'Agent', 'Server' or 'DeploymentGroup'.
    :type runs_on: list of str
    :param tasks: Sets tasks for the task group.
    :type tasks: list of :class:`TaskGroupStep <task-agent.v4_1.models.TaskGroupStep>`
    :param version: Sets version of the task group.
    :type version: :class:`TaskVersion <task-agent.v4_1.models.TaskVersion>`
    """

    _attribute_map = {
        'author': {'key': 'author', 'type': 'str'},
        'category': {'key': 'category', 'type': 'str'},
        'comment': {'key': 'comment', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'friendly_name': {'key': 'friendlyName', 'type': 'str'},
        'icon_url': {'key': 'iconUrl', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'inputs': {'key': 'inputs', 'type': '[TaskInputDefinition]'},
        'instance_name_format': {'key': 'instanceNameFormat', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'parent_definition_id': {'key': 'parentDefinitionId', 'type': 'str'},
        'revision': {'key': 'revision', 'type': 'int'},
        'runs_on': {'key': 'runsOn', 'type': '[str]'},
        'tasks': {'key': 'tasks', 'type': '[TaskGroupStep]'},
        'version': {'key': 'version', 'type': 'TaskVersion'}
    }

    def __init__(self, author=None, category=None, comment=None, description=None, friendly_name=None, icon_url=None, id=None, inputs=None, instance_name_format=None, name=None, parent_definition_id=None, revision=None, runs_on=None, tasks=None, version=None):
        super(TaskGroupUpdateParameter, self).__init__()
        self.author = author
        self.category = category
        self.comment = comment
        self.description = description
        self.friendly_name = friendly_name
        self.icon_url = icon_url
        self.id = id
        self.inputs = inputs
        self.instance_name_format = instance_name_format
        self.name = name
        self.parent_definition_id = parent_definition_id
        self.revision = revision
        self.runs_on = runs_on
        self.tasks = tasks
        self.version = version
