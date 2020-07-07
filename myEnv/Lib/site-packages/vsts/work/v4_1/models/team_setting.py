# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .team_settings_data_contract_base import TeamSettingsDataContractBase


class TeamSetting(TeamSettingsDataContractBase):
    """TeamSetting.

    :param _links: Collection of links relevant to resource
    :type _links: :class:`ReferenceLinks <work.v4_1.models.ReferenceLinks>`
    :param url: Full http link to the resource
    :type url: str
    :param backlog_iteration: Backlog Iteration
    :type backlog_iteration: :class:`TeamSettingsIteration <work.v4_1.models.TeamSettingsIteration>`
    :param backlog_visibilities: Information about categories that are visible on the backlog.
    :type backlog_visibilities: dict
    :param bugs_behavior: BugsBehavior (Off, AsTasks, AsRequirements, ...)
    :type bugs_behavior: object
    :param default_iteration: Default Iteration, the iteration used when creating a new work item on the queries page.
    :type default_iteration: :class:`TeamSettingsIteration <work.v4_1.models.TeamSettingsIteration>`
    :param default_iteration_macro: Default Iteration macro (if any)
    :type default_iteration_macro: str
    :param working_days: Days that the team is working
    :type working_days: list of str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'url': {'key': 'url', 'type': 'str'},
        'backlog_iteration': {'key': 'backlogIteration', 'type': 'TeamSettingsIteration'},
        'backlog_visibilities': {'key': 'backlogVisibilities', 'type': '{bool}'},
        'bugs_behavior': {'key': 'bugsBehavior', 'type': 'object'},
        'default_iteration': {'key': 'defaultIteration', 'type': 'TeamSettingsIteration'},
        'default_iteration_macro': {'key': 'defaultIterationMacro', 'type': 'str'},
        'working_days': {'key': 'workingDays', 'type': '[object]'}
    }

    def __init__(self, _links=None, url=None, backlog_iteration=None, backlog_visibilities=None, bugs_behavior=None, default_iteration=None, default_iteration_macro=None, working_days=None):
        super(TeamSetting, self).__init__(_links=_links, url=url)
        self.backlog_iteration = backlog_iteration
        self.backlog_visibilities = backlog_visibilities
        self.bugs_behavior = bugs_behavior
        self.default_iteration = default_iteration
        self.default_iteration_macro = default_iteration_macro
        self.working_days = working_days
