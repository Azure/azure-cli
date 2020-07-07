# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .team_settings_data_contract_base import TeamSettingsDataContractBase


class TeamSettingsIteration(TeamSettingsDataContractBase):
    """TeamSettingsIteration.

    :param _links: Collection of links relevant to resource
    :type _links: :class:`ReferenceLinks <work.v4_1.models.ReferenceLinks>`
    :param url: Full http link to the resource
    :type url: str
    :param attributes: Attributes such as start and end date
    :type attributes: :class:`TeamIterationAttributes <work.v4_1.models.TeamIterationAttributes>`
    :param id: Id of the resource
    :type id: str
    :param name: Name of the resource
    :type name: str
    :param path: Relative path of the iteration
    :type path: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'url': {'key': 'url', 'type': 'str'},
        'attributes': {'key': 'attributes', 'type': 'TeamIterationAttributes'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'path': {'key': 'path', 'type': 'str'}
    }

    def __init__(self, _links=None, url=None, attributes=None, id=None, name=None, path=None):
        super(TeamSettingsIteration, self).__init__(_links=_links, url=url)
        self.attributes = attributes
        self.id = id
        self.name = name
        self.path = path
