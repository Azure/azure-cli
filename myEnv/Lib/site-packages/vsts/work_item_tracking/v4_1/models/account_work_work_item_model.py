# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccountWorkWorkItemModel(Model):
    """AccountWorkWorkItemModel.

    :param assigned_to:
    :type assigned_to: str
    :param changed_date:
    :type changed_date: datetime
    :param id:
    :type id: int
    :param state:
    :type state: str
    :param team_project:
    :type team_project: str
    :param title:
    :type title: str
    :param work_item_type:
    :type work_item_type: str
    """

    _attribute_map = {
        'assigned_to': {'key': 'assignedTo', 'type': 'str'},
        'changed_date': {'key': 'changedDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'int'},
        'state': {'key': 'state', 'type': 'str'},
        'team_project': {'key': 'teamProject', 'type': 'str'},
        'title': {'key': 'title', 'type': 'str'},
        'work_item_type': {'key': 'workItemType', 'type': 'str'}
    }

    def __init__(self, assigned_to=None, changed_date=None, id=None, state=None, team_project=None, title=None, work_item_type=None):
        super(AccountWorkWorkItemModel, self).__init__()
        self.assigned_to = assigned_to
        self.changed_date = changed_date
        self.id = id
        self.state = state
        self.team_project = team_project
        self.title = title
        self.work_item_type = work_item_type
