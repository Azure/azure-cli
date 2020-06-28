# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .task_definition import TaskDefinition


class TaskGroup(TaskDefinition):
    """TaskGroup.

    :param agent_execution:
    :type agent_execution: :class:`TaskExecution <task-agent.v4_1.models.TaskExecution>`
    :param author:
    :type author: str
    :param category:
    :type category: str
    :param contents_uploaded:
    :type contents_uploaded: bool
    :param contribution_identifier:
    :type contribution_identifier: str
    :param contribution_version:
    :type contribution_version: str
    :param data_source_bindings:
    :type data_source_bindings: list of :class:`DataSourceBinding <task-agent.v4_1.models.DataSourceBinding>`
    :param definition_type:
    :type definition_type: str
    :param demands:
    :type demands: list of :class:`object <task-agent.v4_1.models.object>`
    :param deprecated:
    :type deprecated: bool
    :param description:
    :type description: str
    :param disabled:
    :type disabled: bool
    :param execution:
    :type execution: dict
    :param friendly_name:
    :type friendly_name: str
    :param groups:
    :type groups: list of :class:`TaskGroupDefinition <task-agent.v4_1.models.TaskGroupDefinition>`
    :param help_mark_down:
    :type help_mark_down: str
    :param host_type:
    :type host_type: str
    :param icon_url:
    :type icon_url: str
    :param id:
    :type id: str
    :param inputs:
    :type inputs: list of :class:`TaskInputDefinition <task-agent.v4_1.models.TaskInputDefinition>`
    :param instance_name_format:
    :type instance_name_format: str
    :param minimum_agent_version:
    :type minimum_agent_version: str
    :param name:
    :type name: str
    :param output_variables:
    :type output_variables: list of :class:`TaskOutputVariable <task-agent.v4_1.models.TaskOutputVariable>`
    :param package_location:
    :type package_location: str
    :param package_type:
    :type package_type: str
    :param preview:
    :type preview: bool
    :param release_notes:
    :type release_notes: str
    :param runs_on:
    :type runs_on: list of str
    :param satisfies:
    :type satisfies: list of str
    :param server_owned:
    :type server_owned: bool
    :param source_definitions:
    :type source_definitions: list of :class:`TaskSourceDefinition <task-agent.v4_1.models.TaskSourceDefinition>`
    :param source_location:
    :type source_location: str
    :param version:
    :type version: :class:`TaskVersion <task-agent.v4_1.models.TaskVersion>`
    :param visibility:
    :type visibility: list of str
    :param comment: Gets or sets comment.
    :type comment: str
    :param created_by: Gets or sets the identity who created.
    :type created_by: :class:`IdentityRef <task-agent.v4_1.models.IdentityRef>`
    :param created_on: Gets or sets date on which it got created.
    :type created_on: datetime
    :param deleted: Gets or sets as 'true' to indicate as deleted, 'false' otherwise.
    :type deleted: bool
    :param modified_by: Gets or sets the identity who modified.
    :type modified_by: :class:`IdentityRef <task-agent.v4_1.models.IdentityRef>`
    :param modified_on: Gets or sets date on which it got modified.
    :type modified_on: datetime
    :param owner: Gets or sets the owner.
    :type owner: str
    :param parent_definition_id: Gets or sets parent task group Id. This is used while creating a draft task group.
    :type parent_definition_id: str
    :param revision: Gets or sets revision.
    :type revision: int
    :param tasks: Gets or sets the tasks.
    :type tasks: list of :class:`TaskGroupStep <task-agent.v4_1.models.TaskGroupStep>`
    """

    _attribute_map = {
        'agent_execution': {'key': 'agentExecution', 'type': 'TaskExecution'},
        'author': {'key': 'author', 'type': 'str'},
        'category': {'key': 'category', 'type': 'str'},
        'contents_uploaded': {'key': 'contentsUploaded', 'type': 'bool'},
        'contribution_identifier': {'key': 'contributionIdentifier', 'type': 'str'},
        'contribution_version': {'key': 'contributionVersion', 'type': 'str'},
        'data_source_bindings': {'key': 'dataSourceBindings', 'type': '[DataSourceBinding]'},
        'definition_type': {'key': 'definitionType', 'type': 'str'},
        'demands': {'key': 'demands', 'type': '[object]'},
        'deprecated': {'key': 'deprecated', 'type': 'bool'},
        'description': {'key': 'description', 'type': 'str'},
        'disabled': {'key': 'disabled', 'type': 'bool'},
        'execution': {'key': 'execution', 'type': '{object}'},
        'friendly_name': {'key': 'friendlyName', 'type': 'str'},
        'groups': {'key': 'groups', 'type': '[TaskGroupDefinition]'},
        'help_mark_down': {'key': 'helpMarkDown', 'type': 'str'},
        'host_type': {'key': 'hostType', 'type': 'str'},
        'icon_url': {'key': 'iconUrl', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'inputs': {'key': 'inputs', 'type': '[TaskInputDefinition]'},
        'instance_name_format': {'key': 'instanceNameFormat', 'type': 'str'},
        'minimum_agent_version': {'key': 'minimumAgentVersion', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'output_variables': {'key': 'outputVariables', 'type': '[TaskOutputVariable]'},
        'package_location': {'key': 'packageLocation', 'type': 'str'},
        'package_type': {'key': 'packageType', 'type': 'str'},
        'preview': {'key': 'preview', 'type': 'bool'},
        'release_notes': {'key': 'releaseNotes', 'type': 'str'},
        'runs_on': {'key': 'runsOn', 'type': '[str]'},
        'satisfies': {'key': 'satisfies', 'type': '[str]'},
        'server_owned': {'key': 'serverOwned', 'type': 'bool'},
        'source_definitions': {'key': 'sourceDefinitions', 'type': '[TaskSourceDefinition]'},
        'source_location': {'key': 'sourceLocation', 'type': 'str'},
        'version': {'key': 'version', 'type': 'TaskVersion'},
        'visibility': {'key': 'visibility', 'type': '[str]'},
        'comment': {'key': 'comment', 'type': 'str'},
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'deleted': {'key': 'deleted', 'type': 'bool'},
        'modified_by': {'key': 'modifiedBy', 'type': 'IdentityRef'},
        'modified_on': {'key': 'modifiedOn', 'type': 'iso-8601'},
        'owner': {'key': 'owner', 'type': 'str'},
        'parent_definition_id': {'key': 'parentDefinitionId', 'type': 'str'},
        'revision': {'key': 'revision', 'type': 'int'},
        'tasks': {'key': 'tasks', 'type': '[TaskGroupStep]'}
    }

    def __init__(self, agent_execution=None, author=None, category=None, contents_uploaded=None, contribution_identifier=None, contribution_version=None, data_source_bindings=None, definition_type=None, demands=None, deprecated=None, description=None, disabled=None, execution=None, friendly_name=None, groups=None, help_mark_down=None, host_type=None, icon_url=None, id=None, inputs=None, instance_name_format=None, minimum_agent_version=None, name=None, output_variables=None, package_location=None, package_type=None, preview=None, release_notes=None, runs_on=None, satisfies=None, server_owned=None, source_definitions=None, source_location=None, version=None, visibility=None, comment=None, created_by=None, created_on=None, deleted=None, modified_by=None, modified_on=None, owner=None, parent_definition_id=None, revision=None, tasks=None):
        super(TaskGroup, self).__init__(agent_execution=agent_execution, author=author, category=category, contents_uploaded=contents_uploaded, contribution_identifier=contribution_identifier, contribution_version=contribution_version, data_source_bindings=data_source_bindings, definition_type=definition_type, demands=demands, deprecated=deprecated, description=description, disabled=disabled, execution=execution, friendly_name=friendly_name, groups=groups, help_mark_down=help_mark_down, host_type=host_type, icon_url=icon_url, id=id, inputs=inputs, instance_name_format=instance_name_format, minimum_agent_version=minimum_agent_version, name=name, output_variables=output_variables, package_location=package_location, package_type=package_type, preview=preview, release_notes=release_notes, runs_on=runs_on, satisfies=satisfies, server_owned=server_owned, source_definitions=source_definitions, source_location=source_location, version=version, visibility=visibility)
        self.comment = comment
        self.created_by = created_by
        self.created_on = created_on
        self.deleted = deleted
        self.modified_by = modified_by
        self.modified_on = modified_on
        self.owner = owner
        self.parent_definition_id = parent_definition_id
        self.revision = revision
        self.tasks = tasks
