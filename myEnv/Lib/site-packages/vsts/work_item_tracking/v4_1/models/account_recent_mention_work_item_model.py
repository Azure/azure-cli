# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccountRecentMentionWorkItemModel(Model):
    """AccountRecentMentionWorkItemModel.

    :param assigned_to: Assigned To
    :type assigned_to: str
    :param id: Work Item Id
    :type id: int
    :param mentioned_date_field: Lastest date that the user were mentioned
    :type mentioned_date_field: datetime
    :param state: State of the work item
    :type state: str
    :param team_project: Team project the work item belongs to
    :type team_project: str
    :param title: Title of the work item
    :type title: str
    :param work_item_type: Type of Work Item
    :type work_item_type: str
    """

    _attribute_map = {
        'assigned_to': {'key': 'assignedTo', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'mentioned_date_field': {'key': 'mentionedDateField', 'type': 'iso-8601'},
        'state': {'key': 'state', 'type': 'str'},
        'team_project': {'key': 'teamProject', 'type': 'str'},
        'title': {'key': 'title', 'type': 'str'},
        'work_item_type': {'key': 'workItemType', 'type': 'str'}
    }

    def __init__(self, assigned_to=None, id=None, mentioned_date_field=None, state=None, team_project=None, title=None, work_item_type=None):
        super(AccountRecentMentionWorkItemModel, self).__init__()
        self.assigned_to = assigned_to
        self.id = id
        self.mentioned_date_field = mentioned_date_field
        self.state = state
        self.team_project = team_project
        self.title = title
        self.work_item_type = work_item_type
