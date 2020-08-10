# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProcessConfiguration(Model):
    """ProcessConfiguration.

    :param bug_work_items: Details about bug work items
    :type bug_work_items: :class:`CategoryConfiguration <work.v4_1.models.CategoryConfiguration>`
    :param portfolio_backlogs: Details about portfolio backlogs
    :type portfolio_backlogs: list of :class:`CategoryConfiguration <work.v4_1.models.CategoryConfiguration>`
    :param requirement_backlog: Details of requirement backlog
    :type requirement_backlog: :class:`CategoryConfiguration <work.v4_1.models.CategoryConfiguration>`
    :param task_backlog: Details of task backlog
    :type task_backlog: :class:`CategoryConfiguration <work.v4_1.models.CategoryConfiguration>`
    :param type_fields: Type fields for the process configuration
    :type type_fields: dict
    :param url:
    :type url: str
    """

    _attribute_map = {
        'bug_work_items': {'key': 'bugWorkItems', 'type': 'CategoryConfiguration'},
        'portfolio_backlogs': {'key': 'portfolioBacklogs', 'type': '[CategoryConfiguration]'},
        'requirement_backlog': {'key': 'requirementBacklog', 'type': 'CategoryConfiguration'},
        'task_backlog': {'key': 'taskBacklog', 'type': 'CategoryConfiguration'},
        'type_fields': {'key': 'typeFields', 'type': '{WorkItemFieldReference}'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, bug_work_items=None, portfolio_backlogs=None, requirement_backlog=None, task_backlog=None, type_fields=None, url=None):
        super(ProcessConfiguration, self).__init__()
        self.bug_work_items = bug_work_items
        self.portfolio_backlogs = portfolio_backlogs
        self.requirement_backlog = requirement_backlog
        self.task_backlog = task_backlog
        self.type_fields = type_fields
        self.url = url
