# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class RepositoryLanguageAnalytics(Model):
    """RepositoryLanguageAnalytics.

    :param id:
    :type id: str
    :param language_breakdown:
    :type language_breakdown: list of :class:`LanguageStatistics <project-analysis.v4_0.models.LanguageStatistics>`
    :param name:
    :type name: str
    :param result_phase:
    :type result_phase: object
    :param updated_time:
    :type updated_time: datetime
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'language_breakdown': {'key': 'languageBreakdown', 'type': '[LanguageStatistics]'},
        'name': {'key': 'name', 'type': 'str'},
        'result_phase': {'key': 'resultPhase', 'type': 'object'},
        'updated_time': {'key': 'updatedTime', 'type': 'iso-8601'}
    }

    def __init__(self, id=None, language_breakdown=None, name=None, result_phase=None, updated_time=None):
        super(RepositoryLanguageAnalytics, self).__init__()
        self.id = id
        self.language_breakdown = language_breakdown
        self.name = name
        self.result_phase = result_phase
        self.updated_time = updated_time
