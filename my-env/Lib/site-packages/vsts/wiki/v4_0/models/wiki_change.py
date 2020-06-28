# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WikiChange(Model):
    """WikiChange.

    :param change_type: ChangeType associated with the item in this change.
    :type change_type: object
    :param content: New content of the item.
    :type content: str
    :param item: Item that is subject to this change.
    :type item: object
    """

    _attribute_map = {
        'change_type': {'key': 'changeType', 'type': 'object'},
        'content': {'key': 'content', 'type': 'str'},
        'item': {'key': 'item', 'type': 'object'}
    }

    def __init__(self, change_type=None, content=None, item=None):
        super(WikiChange, self).__init__()
        self.change_type = change_type
        self.content = content
        self.item = item
