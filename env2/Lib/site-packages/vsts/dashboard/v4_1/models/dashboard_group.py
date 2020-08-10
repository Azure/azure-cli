# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DashboardGroup(Model):
    """DashboardGroup.

    :param _links:
    :type _links: :class:`ReferenceLinks <dashboard.v4_1.models.ReferenceLinks>`
    :param dashboard_entries: A list of Dashboards held by the Dashboard Group
    :type dashboard_entries: list of :class:`DashboardGroupEntry <dashboard.v4_1.models.DashboardGroupEntry>`
    :param permission: Deprecated: The old permission model describing the level of permissions for the current team. Pre-M125.
    :type permission: object
    :param team_dashboard_permission: A permissions bit mask describing the security permissions of the current team for dashboards. When this permission is the value None, use GroupMemberPermission. Permissions are evaluated based on the presence of a value other than None, else the GroupMemberPermission will be saved.
    :type team_dashboard_permission: object
    :param url:
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'dashboard_entries': {'key': 'dashboardEntries', 'type': '[DashboardGroupEntry]'},
        'permission': {'key': 'permission', 'type': 'object'},
        'team_dashboard_permission': {'key': 'teamDashboardPermission', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, dashboard_entries=None, permission=None, team_dashboard_permission=None, url=None):
        super(DashboardGroup, self).__init__()
        self._links = _links
        self.dashboard_entries = dashboard_entries
        self.permission = permission
        self.team_dashboard_permission = team_dashboard_permission
        self.url = url
