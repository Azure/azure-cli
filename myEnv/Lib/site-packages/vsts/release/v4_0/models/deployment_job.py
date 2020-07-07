# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DeploymentJob(Model):
    """DeploymentJob.

    :param job:
    :type job: :class:`ReleaseTask <release.v4_0.models.ReleaseTask>`
    :param tasks:
    :type tasks: list of :class:`ReleaseTask <release.v4_0.models.ReleaseTask>`
    """

    _attribute_map = {
        'job': {'key': 'job', 'type': 'ReleaseTask'},
        'tasks': {'key': 'tasks', 'type': '[ReleaseTask]'}
    }

    def __init__(self, job=None, tasks=None):
        super(DeploymentJob, self).__init__()
        self.job = job
        self.tasks = tasks
