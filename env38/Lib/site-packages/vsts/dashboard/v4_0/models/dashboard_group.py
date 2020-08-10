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
    :type _links: :class:`ReferenceLinks <dashboard.v4_0.models.ReferenceLinks>`
    :param dashboard_entries:
    :type dashboard_entries: list of :class:`DashboardGroupEntry <dashboard.v4_0.models.DashboardGroupEntry>`
    :param permission:
    :type permission: object
    :param url:
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'dashboard_entries': {'key': 'dashboardEntries', 'type': '[DashboardGroupEntry]'},
        'permission': {'key': 'permission', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, dashboard_entries=None, permission=None, url=None):
        super(DashboardGroup, self).__init__()
        self._links = _links
        self.dashboard_entries = dashboard_entries
        self.permission = permission
        self.url = url
