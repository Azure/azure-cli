# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Dashboard(Model):
    """Dashboard.

    :param _links:
    :type _links: :class:`ReferenceLinks <dashboard.v4_0.models.ReferenceLinks>`
    :param description:
    :type description: str
    :param eTag:
    :type eTag: str
    :param id:
    :type id: str
    :param name:
    :type name: str
    :param owner_id: Owner for a dashboard. For any legacy dashboards, this would be the unique identifier for the team associated with the dashboard.
    :type owner_id: str
    :param position:
    :type position: int
    :param refresh_interval:
    :type refresh_interval: int
    :param url:
    :type url: str
    :param widgets:
    :type widgets: list of :class:`Widget <dashboard.v4_0.models.Widget>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'description': {'key': 'description', 'type': 'str'},
        'eTag': {'key': 'eTag', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'owner_id': {'key': 'ownerId', 'type': 'str'},
        'position': {'key': 'position', 'type': 'int'},
        'refresh_interval': {'key': 'refreshInterval', 'type': 'int'},
        'url': {'key': 'url', 'type': 'str'},
        'widgets': {'key': 'widgets', 'type': '[Widget]'}
    }

    def __init__(self, _links=None, description=None, eTag=None, id=None, name=None, owner_id=None, position=None, refresh_interval=None, url=None, widgets=None):
        super(Dashboard, self).__init__()
        self._links = _links
        self.description = description
        self.eTag = eTag
        self.id = id
        self.name = name
        self.owner_id = owner_id
        self.position = position
        self.refresh_interval = refresh_interval
        self.url = url
        self.widgets = widgets
