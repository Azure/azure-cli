# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .pick_list_metadata_model import PickListMetadataModel


class PickListModel(PickListMetadataModel):
    """PickListModel.

    :param id: ID of the picklist
    :type id: str
    :param is_suggested: Is input values by user only limited to suggested values
    :type is_suggested: bool
    :param name: Name of the picklist
    :type name: str
    :param type: Type of picklist
    :type type: str
    :param url: Url of the picklist
    :type url: str
    :param items: A list of PicklistItemModel
    :type items: list of :class:`PickListItemModel <work-item-tracking.v4_1.models.PickListItemModel>`
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'is_suggested': {'key': 'isSuggested', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'items': {'key': 'items', 'type': '[PickListItemModel]'}
    }

    def __init__(self, id=None, is_suggested=None, name=None, type=None, url=None, items=None):
        super(PickListModel, self).__init__(id=id, is_suggested=is_suggested, name=name, type=type, url=url)
        self.items = items
