# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DeploymentAttempt(Model):
    """DeploymentAttempt.

    :param attempt:
    :type attempt: int
    :param deployment_id:
    :type deployment_id: int
    :param error_log: Error log to show any unexpected error that occurred during executing deploy step
    :type error_log: str
    :param has_started: Specifies whether deployment has started or not
    :type has_started: bool
    :param id:
    :type id: int
    :param job:
    :type job: :class:`ReleaseTask <release.v4_0.models.ReleaseTask>`
    :param last_modified_by:
    :type last_modified_by: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param last_modified_on:
    :type last_modified_on: datetime
    :param operation_status:
    :type operation_status: object
    :param queued_on:
    :type queued_on: datetime
    :param reason:
    :type reason: object
    :param release_deploy_phases:
    :type release_deploy_phases: list of :class:`ReleaseDeployPhase <release.v4_0.models.ReleaseDeployPhase>`
    :param requested_by:
    :type requested_by: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param requested_for:
    :type requested_for: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param run_plan_id:
    :type run_plan_id: str
    :param status:
    :type status: object
    :param tasks:
    :type tasks: list of :class:`ReleaseTask <release.v4_0.models.ReleaseTask>`
    """

    _attribute_map = {
        'attempt': {'key': 'attempt', 'type': 'int'},
        'deployment_id': {'key': 'deploymentId', 'type': 'int'},
        'error_log': {'key': 'errorLog', 'type': 'str'},
        'has_started': {'key': 'hasStarted', 'type': 'bool'},
        'id': {'key': 'id', 'type': 'int'},
        'job': {'key': 'job', 'type': 'ReleaseTask'},
        'last_modified_by': {'key': 'lastModifiedBy', 'type': 'IdentityRef'},
        'last_modified_on': {'key': 'lastModifiedOn', 'type': 'iso-8601'},
        'operation_status': {'key': 'operationStatus', 'type': 'object'},
        'queued_on': {'key': 'queuedOn', 'type': 'iso-8601'},
        'reason': {'key': 'reason', 'type': 'object'},
        'release_deploy_phases': {'key': 'releaseDeployPhases', 'type': '[ReleaseDeployPhase]'},
        'requested_by': {'key': 'requestedBy', 'type': 'IdentityRef'},
        'requested_for': {'key': 'requestedFor', 'type': 'IdentityRef'},
        'run_plan_id': {'key': 'runPlanId', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'},
        'tasks': {'key': 'tasks', 'type': '[ReleaseTask]'}
    }

    def __init__(self, attempt=None, deployment_id=None, error_log=None, has_started=None, id=None, job=None, last_modified_by=None, last_modified_on=None, operation_status=None, queued_on=None, reason=None, release_deploy_phases=None, requested_by=None, requested_for=None, run_plan_id=None, status=None, tasks=None):
        super(DeploymentAttempt, self).__init__()
        self.attempt = attempt
        self.deployment_id = deployment_id
        self.error_log = error_log
        self.has_started = has_started
        self.id = id
        self.job = job
        self.last_modified_by = last_modified_by
        self.last_modified_on = last_modified_on
        self.operation_status = operation_status
        self.queued_on = queued_on
        self.reason = reason
        self.release_deploy_phases = release_deploy_phases
        self.requested_by = requested_by
        self.requested_for = requested_for
        self.run_plan_id = run_plan_id
        self.status = status
        self.tasks = tasks
