# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .release_definition_environment_step import ReleaseDefinitionEnvironmentStep


class ReleaseDefinitionDeployStep(ReleaseDefinitionEnvironmentStep):
    """ReleaseDefinitionDeployStep.

    :param id:
    :type id: int
    :param tasks: The list of steps for this definition.
    :type tasks: list of :class:`WorkflowTask <release.v4_0.models.WorkflowTask>`
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'tasks': {'key': 'tasks', 'type': '[WorkflowTask]'}
    }

    def __init__(self, id=None, tasks=None):
        super(ReleaseDefinitionDeployStep, self).__init__(id=id)
        self.tasks = tasks
