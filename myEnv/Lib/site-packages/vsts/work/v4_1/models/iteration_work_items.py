# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .team_settings_data_contract_base import TeamSettingsDataContractBase


class IterationWorkItems(TeamSettingsDataContractBase):
    """IterationWorkItems.

    :param _links: Collection of links relevant to resource
    :type _links: :class:`ReferenceLinks <work.v4_1.models.ReferenceLinks>`
    :param url: Full http link to the resource
    :type url: str
    :param work_item_relations: Work item relations
    :type work_item_relations: list of :class:`WorkItemLink <work.v4_1.models.WorkItemLink>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'url': {'key': 'url', 'type': 'str'},
        'work_item_relations': {'key': 'workItemRelations', 'type': '[WorkItemLink]'}
    }

    def __init__(self, _links=None, url=None, work_item_relations=None):
        super(IterationWorkItems, self).__init__(_links=_links, url=url)
        self.work_item_relations = work_item_relations
