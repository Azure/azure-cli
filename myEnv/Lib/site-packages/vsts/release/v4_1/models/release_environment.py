# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseEnvironment(Model):
    """ReleaseEnvironment.

    :param conditions: Gets list of conditions.
    :type conditions: list of :class:`ReleaseCondition <release.v4_1.models.ReleaseCondition>`
    :param created_on: Gets date on which it got created.
    :type created_on: datetime
    :param definition_environment_id: Gets definition environment id.
    :type definition_environment_id: int
    :param demands: Gets demands.
    :type demands: list of :class:`object <release.v4_1.models.object>`
    :param deploy_phases_snapshot: Gets list of deploy phases snapshot.
    :type deploy_phases_snapshot: list of :class:`object <release.v4_1.models.object>`
    :param deploy_steps: Gets deploy steps.
    :type deploy_steps: list of :class:`DeploymentAttempt <release.v4_1.models.DeploymentAttempt>`
    :param environment_options: Gets environment options.
    :type environment_options: :class:`EnvironmentOptions <release.v4_1.models.EnvironmentOptions>`
    :param id: Gets the unique identifier of this field.
    :type id: int
    :param modified_on: Gets date on which it got modified.
    :type modified_on: datetime
    :param name: Gets name.
    :type name: str
    :param next_scheduled_utc_time: Gets next scheduled UTC time.
    :type next_scheduled_utc_time: datetime
    :param owner: Gets the identity who is owner for release environment.
    :type owner: :class:`IdentityRef <release.v4_1.models.IdentityRef>`
    :param post_approvals_snapshot: Gets list of post deploy approvals snapshot.
    :type post_approvals_snapshot: :class:`ReleaseDefinitionApprovals <release.v4_1.models.ReleaseDefinitionApprovals>`
    :param post_deploy_approvals: Gets list of post deploy approvals.
    :type post_deploy_approvals: list of :class:`ReleaseApproval <release.v4_1.models.ReleaseApproval>`
    :param post_deployment_gates_snapshot:
    :type post_deployment_gates_snapshot: :class:`ReleaseDefinitionGatesStep <release.v4_1.models.ReleaseDefinitionGatesStep>`
    :param pre_approvals_snapshot: Gets list of pre deploy approvals snapshot.
    :type pre_approvals_snapshot: :class:`ReleaseDefinitionApprovals <release.v4_1.models.ReleaseDefinitionApprovals>`
    :param pre_deploy_approvals: Gets list of pre deploy approvals.
    :type pre_deploy_approvals: list of :class:`ReleaseApproval <release.v4_1.models.ReleaseApproval>`
    :param pre_deployment_gates_snapshot:
    :type pre_deployment_gates_snapshot: :class:`ReleaseDefinitionGatesStep <release.v4_1.models.ReleaseDefinitionGatesStep>`
    :param process_parameters: Gets process parameters.
    :type process_parameters: :class:`ProcessParameters <release.v4_1.models.ProcessParameters>`
    :param queue_id: Gets queue id.
    :type queue_id: int
    :param rank: Gets rank.
    :type rank: int
    :param release: Gets release reference which specifies the reference of the release to which this release environment is associated.
    :type release: :class:`ReleaseShallowReference <release.v4_1.models.ReleaseShallowReference>`
    :param release_created_by: Gets the identity who created release.
    :type release_created_by: :class:`IdentityRef <release.v4_1.models.IdentityRef>`
    :param release_definition: Gets releaseDefinitionReference which specifies the reference of the release definition to which this release environment is associated.
    :type release_definition: :class:`ReleaseDefinitionShallowReference <release.v4_1.models.ReleaseDefinitionShallowReference>`
    :param release_description: Gets release description.
    :type release_description: str
    :param release_id: Gets release id.
    :type release_id: int
    :param scheduled_deployment_time: Gets schedule deployment time of release environment.
    :type scheduled_deployment_time: datetime
    :param schedules: Gets list of schedules.
    :type schedules: list of :class:`ReleaseSchedule <release.v4_1.models.ReleaseSchedule>`
    :param status: Gets environment status.
    :type status: object
    :param time_to_deploy: Gets time to deploy.
    :type time_to_deploy: float
    :param trigger_reason: Gets trigger reason.
    :type trigger_reason: str
    :param variable_groups: Gets the list of variable groups.
    :type variable_groups: list of :class:`VariableGroup <release.v4_1.models.VariableGroup>`
    :param variables: Gets the dictionary of variables.
    :type variables: dict
    :param workflow_tasks: Gets list of workflow tasks.
    :type workflow_tasks: list of :class:`WorkflowTask <release.v4_1.models.WorkflowTask>`
    """

    _attribute_map = {
        'conditions': {'key': 'conditions', 'type': '[ReleaseCondition]'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'definition_environment_id': {'key': 'definitionEnvironmentId', 'type': 'int'},
        'demands': {'key': 'demands', 'type': '[object]'},
        'deploy_phases_snapshot': {'key': 'deployPhasesSnapshot', 'type': '[object]'},
        'deploy_steps': {'key': 'deploySteps', 'type': '[DeploymentAttempt]'},
        'environment_options': {'key': 'environmentOptions', 'type': 'EnvironmentOptions'},
        'id': {'key': 'id', 'type': 'int'},
        'modified_on': {'key': 'modifiedOn', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'next_scheduled_utc_time': {'key': 'nextScheduledUtcTime', 'type': 'iso-8601'},
        'owner': {'key': 'owner', 'type': 'IdentityRef'},
        'post_approvals_snapshot': {'key': 'postApprovalsSnapshot', 'type': 'ReleaseDefinitionApprovals'},
        'post_deploy_approvals': {'key': 'postDeployApprovals', 'type': '[ReleaseApproval]'},
        'post_deployment_gates_snapshot': {'key': 'postDeploymentGatesSnapshot', 'type': 'ReleaseDefinitionGatesStep'},
        'pre_approvals_snapshot': {'key': 'preApprovalsSnapshot', 'type': 'ReleaseDefinitionApprovals'},
        'pre_deploy_approvals': {'key': 'preDeployApprovals', 'type': '[ReleaseApproval]'},
        'pre_deployment_gates_snapshot': {'key': 'preDeploymentGatesSnapshot', 'type': 'ReleaseDefinitionGatesStep'},
        'process_parameters': {'key': 'processParameters', 'type': 'ProcessParameters'},
        'queue_id': {'key': 'queueId', 'type': 'int'},
        'rank': {'key': 'rank', 'type': 'int'},
        'release': {'key': 'release', 'type': 'ReleaseShallowReference'},
        'release_created_by': {'key': 'releaseCreatedBy', 'type': 'IdentityRef'},
        'release_definition': {'key': 'releaseDefinition', 'type': 'ReleaseDefinitionShallowReference'},
        'release_description': {'key': 'releaseDescription', 'type': 'str'},
        'release_id': {'key': 'releaseId', 'type': 'int'},
        'scheduled_deployment_time': {'key': 'scheduledDeploymentTime', 'type': 'iso-8601'},
        'schedules': {'key': 'schedules', 'type': '[ReleaseSchedule]'},
        'status': {'key': 'status', 'type': 'object'},
        'time_to_deploy': {'key': 'timeToDeploy', 'type': 'float'},
        'trigger_reason': {'key': 'triggerReason', 'type': 'str'},
        'variable_groups': {'key': 'variableGroups', 'type': '[VariableGroup]'},
        'variables': {'key': 'variables', 'type': '{ConfigurationVariableValue}'},
        'workflow_tasks': {'key': 'workflowTasks', 'type': '[WorkflowTask]'}
    }

    def __init__(self, conditions=None, created_on=None, definition_environment_id=None, demands=None, deploy_phases_snapshot=None, deploy_steps=None, environment_options=None, id=None, modified_on=None, name=None, next_scheduled_utc_time=None, owner=None, post_approvals_snapshot=None, post_deploy_approvals=None, post_deployment_gates_snapshot=None, pre_approvals_snapshot=None, pre_deploy_approvals=None, pre_deployment_gates_snapshot=None, process_parameters=None, queue_id=None, rank=None, release=None, release_created_by=None, release_definition=None, release_description=None, release_id=None, scheduled_deployment_time=None, schedules=None, status=None, time_to_deploy=None, trigger_reason=None, variable_groups=None, variables=None, workflow_tasks=None):
        super(ReleaseEnvironment, self).__init__()
        self.conditions = conditions
        self.created_on = created_on
        self.definition_environment_id = definition_environment_id
        self.demands = demands
        self.deploy_phases_snapshot = deploy_phases_snapshot
        self.deploy_steps = deploy_steps
        self.environment_options = environment_options
        self.id = id
        self.modified_on = modified_on
        self.name = name
        self.next_scheduled_utc_time = next_scheduled_utc_time
        self.owner = owner
        self.post_approvals_snapshot = post_approvals_snapshot
        self.post_deploy_approvals = post_deploy_approvals
        self.post_deployment_gates_snapshot = post_deployment_gates_snapshot
        self.pre_approvals_snapshot = pre_approvals_snapshot
        self.pre_deploy_approvals = pre_deploy_approvals
        self.pre_deployment_gates_snapshot = pre_deployment_gates_snapshot
        self.process_parameters = process_parameters
        self.queue_id = queue_id
        self.rank = rank
        self.release = release
        self.release_created_by = release_created_by
        self.release_definition = release_definition
        self.release_description = release_description
        self.release_id = release_id
        self.scheduled_deployment_time = scheduled_deployment_time
        self.schedules = schedules
        self.status = status
        self.time_to_deploy = time_to_deploy
        self.trigger_reason = trigger_reason
        self.variable_groups = variable_groups
        self.variables = variables
        self.workflow_tasks = workflow_tasks
