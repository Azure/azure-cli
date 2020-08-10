# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ManualIntervention(Model):
    """ManualIntervention.

    :param approver: Gets or sets the identity who should approve.
    :type approver: :class:`IdentityRef <release.v4_1.models.IdentityRef>`
    :param comments: Gets or sets comments for approval.
    :type comments: str
    :param created_on: Gets date on which it got created.
    :type created_on: datetime
    :param id: Gets the unique identifier for manual intervention.
    :type id: int
    :param instructions: Gets or sets instructions for approval.
    :type instructions: str
    :param modified_on: Gets date on which it got modified.
    :type modified_on: datetime
    :param name: Gets or sets the name.
    :type name: str
    :param release: Gets releaseReference for manual intervention.
    :type release: :class:`ReleaseShallowReference <release.v4_1.models.ReleaseShallowReference>`
    :param release_definition: Gets releaseDefinitionReference for manual intervention.
    :type release_definition: :class:`ReleaseDefinitionShallowReference <release.v4_1.models.ReleaseDefinitionShallowReference>`
    :param release_environment: Gets releaseEnvironmentReference for manual intervention.
    :type release_environment: :class:`ReleaseEnvironmentShallowReference <release.v4_1.models.ReleaseEnvironmentShallowReference>`
    :param status: Gets or sets the status of the manual intervention.
    :type status: object
    :param task_instance_id: Get task instance identifier.
    :type task_instance_id: str
    :param url: Gets url to access the manual intervention.
    :type url: str
    """

    _attribute_map = {
        'approver': {'key': 'approver', 'type': 'IdentityRef'},
        'comments': {'key': 'comments', 'type': 'str'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'int'},
        'instructions': {'key': 'instructions', 'type': 'str'},
        'modified_on': {'key': 'modifiedOn', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'release': {'key': 'release', 'type': 'ReleaseShallowReference'},
        'release_definition': {'key': 'releaseDefinition', 'type': 'ReleaseDefinitionShallowReference'},
        'release_environment': {'key': 'releaseEnvironment', 'type': 'ReleaseEnvironmentShallowReference'},
        'status': {'key': 'status', 'type': 'object'},
        'task_instance_id': {'key': 'taskInstanceId', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, approver=None, comments=None, created_on=None, id=None, instructions=None, modified_on=None, name=None, release=None, release_definition=None, release_environment=None, status=None, task_instance_id=None, url=None):
        super(ManualIntervention, self).__init__()
        self.approver = approver
        self.comments = comments
        self.created_on = created_on
        self.id = id
        self.instructions = instructions
        self.modified_on = modified_on
        self.name = name
        self.release = release
        self.release_definition = release_definition
        self.release_environment = release_environment
        self.status = status
        self.task_instance_id = task_instance_id
        self.url = url
