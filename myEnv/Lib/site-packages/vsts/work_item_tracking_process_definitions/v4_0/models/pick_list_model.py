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

    :param id:
    :type id: str
    :param is_suggested:
    :type is_suggested: bool
    :param name:
    :type name: str
    :param type:
    :type type: str
    :param url:
    :type url: str
    :param items:
    :type items: list of :class:`PickListItemModel <work-item-tracking.v4_0.models.PickListItemModel>`
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
