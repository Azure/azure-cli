# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .wiki_change import WikiChange


class WikiPageChange(WikiChange):
    """WikiPageChange.

    :param original_order: Original order of the page to be provided in case of reorder or rename.
    :type original_order: int
    :param original_path: Original path of the page to be provided in case of rename.
    :type original_path: str
    """

    _attribute_map = {
        'original_order': {'key': 'originalOrder', 'type': 'int'},
        'original_path': {'key': 'originalPath', 'type': 'str'}
    }

    def __init__(self, original_order=None, original_path=None):
        super(WikiPageChange, self).__init__()
        self.original_order = original_order
        self.original_path = original_path
