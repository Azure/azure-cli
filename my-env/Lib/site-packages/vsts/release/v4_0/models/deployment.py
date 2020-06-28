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

    :param _links:
    :type _links: :class:`ReferenceLinks <release.v4_0.models.ReferenceLinks>`
    :param attempt:
    :type attempt: int
    :param conditions:
    :type conditions: list of :class:`Condition <release.v4_0.models.Condition>`
    :param definition_environment_id:
    :type definition_environment_id: int
    :param deployment_status:
    :type deployment_status: object
    :param id:
    :type id: int
    :param last_modified_by:
    :type last_modified_by: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param last_modified_on:
    :type last_modified_on: datetime
    :param operation_status:
    :type operation_status: object
    :param post_deploy_approvals:
    :type post_deploy_approvals: list of :class:`ReleaseApproval <release.v4_0.models.ReleaseApproval>`
    :param pre_deploy_approvals:
    :type pre_deploy_approvals: list of :class:`ReleaseApproval <release.v4_0.models.ReleaseApproval>`
    :param queued_on:
    :type queued_on: datetime
    :param reason:
    :type reason: object
    :param release:
    :type release: :class:`ReleaseReference <release.v4_0.models.ReleaseReference>`
    :param release_definition:
    :type release_definition: :class:`ReleaseDefinitionShallowReference <release.v4_0.models.ReleaseDefinitionShallowReference>`
    :param release_environment:
    :type release_environment: :class:`ReleaseEnvironmentShallowReference <release.v4_0.models.ReleaseEnvironmentShallowReference>`
    :param requested_by:
    :type requested_by: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param requested_for:
    :type requested_for: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param scheduled_deployment_time:
    :type scheduled_deployment_time: datetime
    :param started_on:
    :type started_on: datetime
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'attempt': {'key': 'attempt', 'type': 'int'},
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

    def __init__(self, _links=None, attempt=None, conditions=None, definition_environment_id=None, deployment_status=None, id=None, last_modified_by=None, last_modified_on=None, operation_status=None, post_deploy_approvals=None, pre_deploy_approvals=None, queued_on=None, reason=None, release=None, release_definition=None, release_environment=None, requested_by=None, requested_for=None, scheduled_deployment_time=None, started_on=None):
        super(Deployment, self).__init__()
        self._links = _links
        self.attempt = attempt
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
