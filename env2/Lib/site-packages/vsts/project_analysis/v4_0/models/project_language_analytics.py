# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProjectLanguageAnalytics(Model):
    """ProjectLanguageAnalytics.

    :param id:
    :type id: str
    :param language_breakdown:
    :type language_breakdown: list of :class:`LanguageStatistics <project-analysis.v4_0.models.LanguageStatistics>`
    :param repository_language_analytics:
    :type repository_language_analytics: list of :class:`RepositoryLanguageAnalytics <project-analysis.v4_0.models.RepositoryLanguageAnalytics>`
    :param result_phase:
    :type result_phase: object
    :param url:
    :type url: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'language_breakdown': {'key': 'languageBreakdown', 'type': '[LanguageStatistics]'},
        'repository_language_analytics': {'key': 'repositoryLanguageAnalytics', 'type': '[RepositoryLanguageAnalytics]'},
        'result_phase': {'key': 'resultPhase', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, id=None, language_breakdown=None, repository_language_analytics=None, result_phase=None, url=None):
        super(ProjectLanguageAnalytics, self).__init__()
        self.id = id
        self.language_breakdown = language_breakdown
        self.repository_language_analytics = repository_language_analytics
        self.result_phase = result_phase
        self.url = url
