# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .wiki_page_move_parameters import WikiPageMoveParameters


class WikiPageMove(WikiPageMoveParameters):
    """WikiPageMove.

    :param new_order: New order of the wiki page.
    :type new_order: int
    :param new_path: New path of the wiki page.
    :type new_path: str
    :param path: Current path of the wiki page.
    :type path: str
    :param page: Resultant page of this page move operation.
    :type page: :class:`WikiPage <wiki.v4_1.models.WikiPage>`
    """

    _attribute_map = {
        'new_order': {'key': 'newOrder', 'type': 'int'},
        'new_path': {'key': 'newPath', 'type': 'str'},
        'path': {'key': 'path', 'type': 'str'},
        'page': {'key': 'page', 'type': 'WikiPage'}
    }

    def __init__(self, new_order=None, new_path=None, path=None, page=None):
        super(WikiPageMove, self).__init__(new_order=new_order, new_path=new_path, path=path)
        self.page = page
