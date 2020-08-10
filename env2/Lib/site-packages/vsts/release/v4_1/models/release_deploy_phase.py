# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseDeployPhase(Model):
    """ReleaseDeployPhase.

    :param deployment_jobs:
    :type deployment_jobs: list of :class:`DeploymentJob <release.v4_1.models.DeploymentJob>`
    :param error_log:
    :type error_log: str
    :param id:
    :type id: int
    :param manual_interventions:
    :type manual_interventions: list of :class:`ManualIntervention <release.v4_1.models.ManualIntervention>`
    :param name:
    :type name: str
    :param phase_id:
    :type phase_id: str
    :param phase_type:
    :type phase_type: object
    :param rank:
    :type rank: int
    :param run_plan_id:
    :type run_plan_id: str
    :param status:
    :type status: object
    """

    _attribute_map = {
        'deployment_jobs': {'key': 'deploymentJobs', 'type': '[DeploymentJob]'},
        'error_log': {'key': 'errorLog', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'manual_interventions': {'key': 'manualInterventions', 'type': '[ManualIntervention]'},
        'name': {'key': 'name', 'type': 'str'},
        'phase_id': {'key': 'phaseId', 'type': 'str'},
        'phase_type': {'key': 'phaseType', 'type': 'object'},
        'rank': {'key': 'rank', 'type': 'int'},
        'run_plan_id': {'key': 'runPlanId', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'}
    }

    def __init__(self, deployment_jobs=None, error_log=None, id=None, manual_interventions=None, name=None, phase_id=None, phase_type=None, rank=None, run_plan_id=None, status=None):
        super(ReleaseDeployPhase, self).__init__()
        self.deployment_jobs = deployment_jobs
        self.error_log = error_log
        self.id = id
        self.manual_interventions = manual_interventions
        self.name = name
        self.phase_id = phase_id
        self.phase_type = phase_type
        self.rank = rank
        self.run_plan_id = run_plan_id
        self.status = status
