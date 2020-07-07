# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BacklogConfiguration(Model):
    """BacklogConfiguration.

    :param backlog_fields: Behavior/type field mapping
    :type backlog_fields: :class:`BacklogFields <work.v4_0.models.BacklogFields>`
    :param bugs_behavior: Bugs behavior
    :type bugs_behavior: object
    :param hidden_backlogs: Hidden Backlog
    :type hidden_backlogs: list of str
    :param portfolio_backlogs: Portfolio backlog descriptors
    :type portfolio_backlogs: list of :class:`BacklogLevelConfiguration <work.v4_0.models.BacklogLevelConfiguration>`
    :param requirement_backlog: Requirement backlog
    :type requirement_backlog: :class:`BacklogLevelConfiguration <work.v4_0.models.BacklogLevelConfiguration>`
    :param task_backlog: Task backlog
    :type task_backlog: :class:`BacklogLevelConfiguration <work.v4_0.models.BacklogLevelConfiguration>`
    :param url:
    :type url: str
    :param work_item_type_mapped_states: Mapped states for work item types
    :type work_item_type_mapped_states: list of :class:`WorkItemTypeStateInfo <work.v4_0.models.WorkItemTypeStateInfo>`
    """

    _attribute_map = {
        'backlog_fields': {'key': 'backlogFields', 'type': 'BacklogFields'},
        'bugs_behavior': {'key': 'bugsBehavior', 'type': 'object'},
        'hidden_backlogs': {'key': 'hiddenBacklogs', 'type': '[str]'},
        'portfolio_backlogs': {'key': 'portfolioBacklogs', 'type': '[BacklogLevelConfiguration]'},
        'requirement_backlog': {'key': 'requirementBacklog', 'type': 'BacklogLevelConfiguration'},
        'task_backlog': {'key': 'taskBacklog', 'type': 'BacklogLevelConfiguration'},
        'url': {'key': 'url', 'type': 'str'},
        'work_item_type_mapped_states': {'key': 'workItemTypeMappedStates', 'type': '[WorkItemTypeStateInfo]'}
    }

    def __init__(self, backlog_fields=None, bugs_behavior=None, hidden_backlogs=None, portfolio_backlogs=None, requirement_backlog=None, task_backlog=None, url=None, work_item_type_mapped_states=None):
        super(BacklogConfiguration, self).__init__()
        self.backlog_fields = backlog_fields
        self.bugs_behavior = bugs_behavior
        self.hidden_backlogs = hidden_backlogs
        self.portfolio_backlogs = portfolio_backlogs
        self.requirement_backlog = requirement_backlog
        self.task_backlog = task_backlog
        self.url = url
        self.work_item_type_mapped_states = work_item_type_mapped_states
