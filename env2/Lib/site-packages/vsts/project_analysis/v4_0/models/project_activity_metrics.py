# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProjectActivityMetrics(Model):
    """ProjectActivityMetrics.

    :param authors_count:
    :type authors_count: int
    :param code_changes_count:
    :type code_changes_count: int
    :param code_changes_trend:
    :type code_changes_trend: list of :class:`CodeChangeTrendItem <project-analysis.v4_0.models.CodeChangeTrendItem>`
    :param project_id:
    :type project_id: str
    :param pull_requests_completed_count:
    :type pull_requests_completed_count: int
    :param pull_requests_created_count:
    :type pull_requests_created_count: int
    """

    _attribute_map = {
        'authors_count': {'key': 'authorsCount', 'type': 'int'},
        'code_changes_count': {'key': 'codeChangesCount', 'type': 'int'},
        'code_changes_trend': {'key': 'codeChangesTrend', 'type': '[CodeChangeTrendItem]'},
        'project_id': {'key': 'projectId', 'type': 'str'},
        'pull_requests_completed_count': {'key': 'pullRequestsCompletedCount', 'type': 'int'},
        'pull_requests_created_count': {'key': 'pullRequestsCreatedCount', 'type': 'int'}
    }

    def __init__(self, authors_count=None, code_changes_count=None, code_changes_trend=None, project_id=None, pull_requests_completed_count=None, pull_requests_created_count=None):
        super(ProjectActivityMetrics, self).__init__()
        self.authors_count = authors_count
        self.code_changes_count = code_changes_count
        self.code_changes_trend = code_changes_trend
        self.project_id = project_id
        self.pull_requests_completed_count = pull_requests_completed_count
        self.pull_requests_created_count = pull_requests_created_count
