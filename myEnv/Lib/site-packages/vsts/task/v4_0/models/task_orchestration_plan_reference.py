# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskOrchestrationPlanReference(Model):
    """TaskOrchestrationPlanReference.

    :param artifact_location:
    :type artifact_location: str
    :param artifact_uri:
    :type artifact_uri: str
    :param definition:
    :type definition: :class:`TaskOrchestrationOwner <task.v4_0.models.TaskOrchestrationOwner>`
    :param owner:
    :type owner: :class:`TaskOrchestrationOwner <task.v4_0.models.TaskOrchestrationOwner>`
    :param plan_id:
    :type plan_id: str
    :param plan_type:
    :type plan_type: str
    :param scope_identifier:
    :type scope_identifier: str
    :param version:
    :type version: int
    """

    _attribute_map = {
        'artifact_location': {'key': 'artifactLocation', 'type': 'str'},
        'artifact_uri': {'key': 'artifactUri', 'type': 'str'},
        'definition': {'key': 'definition', 'type': 'TaskOrchestrationOwner'},
        'owner': {'key': 'owner', 'type': 'TaskOrchestrationOwner'},
        'plan_id': {'key': 'planId', 'type': 'str'},
        'plan_type': {'key': 'planType', 'type': 'str'},
        'scope_identifier': {'key': 'scopeIdentifier', 'type': 'str'},
        'version': {'key': 'version', 'type': 'int'}
    }

    def __init__(self, artifact_location=None, artifact_uri=None, definition=None, owner=None, plan_id=None, plan_type=None, scope_identifier=None, version=None):
        super(TaskOrchestrationPlanReference, self).__init__()
        self.artifact_location = artifact_location
        self.artifact_uri = artifact_uri
        self.definition = definition
        self.owner = owner
        self.plan_id = plan_id
        self.plan_type = plan_type
        self.scope_identifier = scope_identifier
        self.version = version
