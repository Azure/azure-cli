# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Deployment(Model):
    """Deployment.

    :param _links: Gets links to access the deployment.
    :type _links: :class:`ReferenceLinks <release.v4_1.models.ReferenceLinks>`
    :param attempt: Gets attempt number.
    :type attempt: int
    :param completed_on: Gets the date on which deployment is complete.
    :type completed_on: datetime
    :param conditions: Gets the list of condition associated with deployment.
    :type conditions: list of :class:`Condition <release.v4_1.models.Condition>`
    :param definition_environment_id: Gets release definition environment id.
    :type definition_environment_id: int
    :param deployment_status: Gets status of the deployment.
    :type deployment_status: object
    :param id: Gets the unique identifier for deployment.
    :type id: int
    :param last_modified_by: Gets the identity who last modified the deployment.
    :type last_modified_by: :class:`IdentityRef <release.v4_1.models.IdentityRef>`
    :param last_modified_on: Gets the date on which deployment is last modified.
    :type last_modified_on: datetime
    :param operation_status: Gets operation status of deployment.
    :type operation_status: object
    :param post_deploy_approvals: Gets list of PostDeployApprovals.
    :type post_deploy_approvals: list of :class:`ReleaseApproval <release.v4_1.models.ReleaseApproval>`
    :param pre_deploy_approvals: Gets list of PreDeployApprovals.
    :type pre_deploy_approvals: list of :class:`ReleaseApproval <release.v4_1.models.ReleaseApproval>`
    :param queued_on: Gets the date on which deployment is queued.
    :type queued_on: datetime
    :param reason: Gets reason of deployment.
    :type reason: object
    :param release: Gets the reference of release.
    :type release: :class:`ReleaseReference <release.v4_1.models.ReleaseReference>`
    :param release_definition: Gets releaseDefinitionReference which specifies the reference of the release definition to which the deployment is associated.
    :type release_definition: :class:`ReleaseDefinitionShallowReference <release.v4_1.models.ReleaseDefinitionShallowReference>`
    :param release_environment: Gets releaseEnvironmentReference which specifies the reference of the release environment to which the deployment is associated.
    :type release_environment: :class:`ReleaseEnvironmentShallowReference <release.v4_1.models.ReleaseEnvironmentShallowReference>`
    :param requested_by: Gets the identity who requested.
    :type requested_by: :class:`IdentityRef <release.v4_1.models.IdentityRef>`
    :param requested_for: Gets the identity for whom deployment is requested.
    :type requested_for: :class:`IdentityRef <release.v4_1.models.IdentityRef>`
    :param scheduled_deployment_time: Gets the date on which deployment is scheduled.
    :type scheduled_deployment_time: datetime
    :param started_on: Gets the date on which deployment is started.
    :type started_on: datetime
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'attempt': {'key': 'attempt', 'type': 'int'},
        'completed_on': {'key': 'completedOn', 'type': 'iso-8601'},
        'conditions': {'key': 'conditions', 'type': '[Condition]'},
        'definition_environment_id': {'key': 'definitionEnvironmentId', 'type': 'int'},
        'deployment_status': {'key': 'deploymentStatus', 'type': 'object'},
        'id': {'key': 'id', 'type': 'int'},
        'last_modified_by': {'key': 'lastModifiedBy', 'type': 'IdentityRef'},
        'last_modified_on': {'key': 'lastModifiedOn', 'type': 'iso-8601'},
        'operation_status': {'key': 'operationStatus', 'type': 'object'},
        'post_deploy_approvals': {'key': 'postDeployApprovals', 'type': '[ReleaseApproval]'},
        'pre_deploy_approvals': {'key': 'preDeployApprovals', 'type': '[ReleaseApproval]'},
        'queued_on': {'key': 'queuedOn', 'type': 'iso-8601'},
        'reason': {'key': 'reason', 'type': 'object'},
        'release': {'key': 'release', 'type': 'ReleaseReference'},
        'release_definition': {'key': 'releaseDefinition', 'type': 'ReleaseDefinitionShallowReference'},
        'release_environment': {'key': 'releaseEnvironment', 'type': 'ReleaseEnvironmentShallowReference'},
        'requested_by': {'key': 'requestedBy', 'type': 'IdentityRef'},
        'requested_for': {'key': 'requestedFor', 'type': 'IdentityRef'},
        'scheduled_deployment_time': {'key': 'scheduledDeploymentTime', 'type': 'iso-8601'},
        'started_on': {'key': 'startedOn', 'type': 'iso-8601'}
    }

    def __init__(self, _links=None, attempt=None, completed_on=None, conditions=None, definition_environment_id=None, deployment_status=None, id=None, last_modified_by=None, last_modified_on=None, operation_status=None, post_deploy_approvals=None, pre_deploy_approvals=None, queued_on=None, reason=None, release=None, release_definition=None, release_environment=None, requested_by=None, requested_for=None, scheduled_deployment_time=None, started_on=None):
        super(Deployment, self).__init__()
        self._links = _links
        self.attempt = attempt
        self.completed_on = completed_on
        self.conditions = conditions
        self.definition_environment_id = definition_environment_id
        self.deployment_status = deployment_status
        self.id = id
        self.last_modified_by = last_modified_by
        self.last_modified_on = last_modified_on
        self.operation_status = operation_status
        self.post_deploy_approvals = post_deploy_approvals
        self.pre_deploy_approvals = pre_deploy_approvals
        self.queued_on = queued_on
        self.reason = reason
        self.release = release
        self.release_definition = release_definition
        self.release_environment = release_environment
        self.requested_by = requested_by
        self.requested_for = requested_for
        self.scheduled_deployment_time = scheduled_deployment_time
        self.started_on = started_on
