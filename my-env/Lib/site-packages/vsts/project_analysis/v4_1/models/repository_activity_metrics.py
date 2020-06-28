# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class RepositoryActivityMetrics(Model):
    """RepositoryActivityMetrics.

    :param code_changes_count:
    :type code_changes_count: int
    :param code_changes_trend:
    :type code_changes_trend: list of :class:`CodeChangeTrendItem <project-analysis.v4_1.models.CodeChangeTrendItem>`
    :param repository_id:
    :type repository_id: str
    """

    _attribute_map = {
        'code_changes_count': {'key': 'codeChangesCount', 'type': 'int'},
        'code_changes_trend': {'key': 'codeChangesTrend', 'type': '[CodeChangeTrendItem]'},
        'repository_id': {'key': 'repositoryId', 'type': 'str'}
    }

    def __init__(self, code_changes_count=None, code_changes_trend=None, repository_id=None):
        super(RepositoryActivityMetrics, self).__init__()
        self.code_changes_count = code_changes_count
        self.code_changes_trend = code_changes_trend
        self.repository_id = repository_id
