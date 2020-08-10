# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TfvcLabelRequestData(Model):
    """TfvcLabelRequestData.

    :param include_links: Whether to include the _links field on the shallow references
    :type include_links: bool
    :param item_label_filter:
    :type item_label_filter: str
    :param label_scope:
    :type label_scope: str
    :param max_item_count:
    :type max_item_count: int
    :param name:
    :type name: str
    :param owner:
    :type owner: str
    """

    _attribute_map = {
        'include_links': {'key': 'includeLinks', 'type': 'bool'},
        'item_label_filter': {'key': 'itemLabelFilter', 'type': 'str'},
        'label_scope': {'key': 'labelScope', 'type': 'str'},
        'max_item_count': {'key': 'maxItemCount', 'type': 'int'},
        'name': {'key': 'name', 'type': 'str'},
        'owner': {'key': 'owner', 'type': 'str'}
    }

    def __init__(self, include_links=None, item_label_filter=None, label_scope=None, max_item_count=None, name=None, owner=None):
        super(TfvcLabelRequestData, self).__init__()
        self.include_links = include_links
        self.item_label_filter = item_label_filter
        self.label_scope = label_scope
        self.max_item_count = max_item_count
        self.name = name
        self.owner = owner
