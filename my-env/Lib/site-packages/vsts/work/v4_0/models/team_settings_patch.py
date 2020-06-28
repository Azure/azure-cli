# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TeamSettingsPatch(Model):
    """TeamSettingsPatch.

    :param backlog_iteration:
    :type backlog_iteration: str
    :param backlog_visibilities:
    :type backlog_visibilities: dict
    :param bugs_behavior:
    :type bugs_behavior: object
    :param default_iteration:
    :type default_iteration: str
    :param default_iteration_macro:
    :type default_iteration_macro: str
    :param working_days:
    :type working_days: list of str
    """

    _attribute_map = {
        'backlog_iteration': {'key': 'backlogIteration', 'type': 'str'},
        'backlog_visibilities': {'key': 'backlogVisibilities', 'type': '{bool}'},
        'bugs_behavior': {'key': 'bugsBehavior', 'type': 'object'},
        'default_iteration': {'key': 'defaultIteration', 'type': 'str'},
        'default_iteration_macro': {'key': 'defaultIterationMacro', 'type': 'str'},
        'working_days': {'key': 'workingDays', 'type': '[object]'}
    }

    def __init__(self, backlog_iteration=None, backlog_visibilities=None, bugs_behavior=None, default_iteration=None, default_iteration_macro=None, working_days=None):
        super(TeamSettingsPatch, self).__init__()
        self.backlog_iteration = backlog_iteration
        self.backlog_visibilities = backlog_visibilities
        self.bugs_behavior = bugs_behavior
        self.default_iteration = default_iteration
        self.default_iteration_macro = default_iteration_macro
        self.working_days = working_days
