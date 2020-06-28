# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccountRecentActivityWorkItemModel(Model):
    """AccountRecentActivityWorkItemModel.

    :param activity_date: Date of the last Activity by the user
    :type activity_date: datetime
    :param activity_type: Type of the activity
    :type activity_type: object
    :param assigned_to: Assigned To
    :type assigned_to: str
    :param changed_date: Last changed date of the work item
    :type changed_date: datetime
    :param id: Work Item Id
    :type id: int
    :param identity_id: TeamFoundationId of the user this activity belongs to
    :type identity_id: str
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
        'activity_date': {'key': 'activityDate', 'type': 'iso-8601'},
        'activity_type': {'key': 'activityType', 'type': 'object'},
        'assigned_to': {'key': 'assignedTo', 'type': 'str'},
        'changed_date': {'key': 'changedDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'int'},
        'identity_id': {'key': 'identityId', 'type': 'str'},
        'state': {'key': 'state', 'type': 'str'},
        'team_project': {'key': 'teamProject', 'type': 'str'},
        'title': {'key': 'title', 'type': 'str'},
        'work_item_type': {'key': 'workItemType', 'type': 'str'}
    }

    def __init__(self, activity_date=None, activity_type=None, assigned_to=None, changed_date=None, id=None, identity_id=None, state=None, team_project=None, title=None, work_item_type=None):
        super(AccountRecentActivityWorkItemModel, self).__init__()
        self.activity_date = activity_date
        self.activity_type = activity_type
        self.assigned_to = assigned_to
        self.changed_date = changed_date
        self.id = id
        self.identity_id = identity_id
        self.state = state
        self.team_project = team_project
        self.title = title
        self.work_item_type = work_item_type
