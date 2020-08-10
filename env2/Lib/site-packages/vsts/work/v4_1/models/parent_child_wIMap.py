# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ParentChildWIMap(Model):
    """ParentChildWIMap.

    :param child_work_item_ids:
    :type child_work_item_ids: list of int
    :param id:
    :type id: int
    :param title:
    :type title: str
    """

    _attribute_map = {
        'child_work_item_ids': {'key': 'childWorkItemIds', 'type': '[int]'},
        'id': {'key': 'id', 'type': 'int'},
        'title': {'key': 'title', 'type': 'str'}
    }

    def __init__(self, child_work_item_ids=None, id=None, title=None):
        super(ParentChildWIMap, self).__init__()
        self.child_work_item_ids = child_work_item_ids
        self.id = id
        self.title = title
