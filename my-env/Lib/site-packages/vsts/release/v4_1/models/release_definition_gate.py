# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseDefinitionGate(Model):
    """ReleaseDefinitionGate.

    :param tasks:
    :type tasks: list of :class:`WorkflowTask <release.v4_1.models.WorkflowTask>`
    """

    _attribute_map = {
        'tasks': {'key': 'tasks', 'type': '[WorkflowTask]'}
    }

    def __init__(self, tasks=None):
        super(ReleaseDefinitionGate, self).__init__()
        self.tasks = tasks
