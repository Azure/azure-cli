# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseGates(Model):
    """ReleaseGates.

    :param deployment_jobs:
    :type deployment_jobs: list of :class:`DeploymentJob <release.v4_1.models.DeploymentJob>`
    :param id:
    :type id: int
    :param last_modified_on:
    :type last_modified_on: datetime
    :param run_plan_id:
    :type run_plan_id: str
    :param stabilization_completed_on:
    :type stabilization_completed_on: datetime
    :param started_on:
    :type started_on: datetime
    :param status:
    :type status: object
    """

    _attribute_map = {
        'deployment_jobs': {'key': 'deploymentJobs', 'type': '[DeploymentJob]'},
        'id': {'key': 'id', 'type': 'int'},
        'last_modified_on': {'key': 'lastModifiedOn', 'type': 'iso-8601'},
        'run_plan_id': {'key': 'runPlanId', 'type': 'str'},
        'stabilization_completed_on': {'key': 'stabilizationCompletedOn', 'type': 'iso-8601'},
        'started_on': {'key': 'startedOn', 'type': 'iso-8601'},
        'status': {'key': 'status', 'type': 'object'}
    }

    def __init__(self, deployment_jobs=None, id=None, last_modified_on=None, run_plan_id=None, stabilization_completed_on=None, started_on=None, status=None):
        super(ReleaseGates, self).__init__()
        self.deployment_jobs = deployment_jobs
        self.id = id
        self.last_modified_on = last_modified_on
        self.run_plan_id = run_plan_id
        self.stabilization_completed_on = stabilization_completed_on
        self.started_on = started_on
        self.status = status
