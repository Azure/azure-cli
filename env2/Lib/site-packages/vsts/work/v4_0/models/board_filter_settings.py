# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BoardFilterSettings(Model):
    """BoardFilterSettings.

    :param criteria:
    :type criteria: :class:`FilterModel <work.v4_0.models.FilterModel>`
    :param parent_work_item_ids:
    :type parent_work_item_ids: list of int
    :param query_text:
    :type query_text: str
    """

    _attribute_map = {
        'criteria': {'key': 'criteria', 'type': 'FilterModel'},
        'parent_work_item_ids': {'key': 'parentWorkItemIds', 'type': '[int]'},
        'query_text': {'key': 'queryText', 'type': 'str'}
    }

    def __init__(self, criteria=None, parent_work_item_ids=None, query_text=None):
        super(BoardFilterSettings, self).__init__()
        self.criteria = criteria
        self.parent_work_item_ids = parent_work_item_ids
        self.query_text = query_text
