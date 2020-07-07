# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WikiPage(Model):
    """WikiPage.

    :param depth: The depth in terms of level in the hierarchy.
    :type depth: int
    :param git_item_path: The path of the item corresponding to the wiki page stored in the backing Git repository. This is populated only in the response of the wiki pages GET API.
    :type git_item_path: str
    :param is_non_conformant: Flag to denote if a page is non-conforming, i.e. 1) if the name doesn't match our norms. 2) if the page does not have a valid entry in the appropriate order file.
    :type is_non_conformant: bool
    :param is_parent_page: Returns true if this page has child pages under its path.
    :type is_parent_page: bool
    :param order: Order associated with the page with respect to other pages in the same hierarchy level.
    :type order: int
    :param path: Path of the wiki page.
    :type path: str
    """

    _attribute_map = {
        'depth': {'key': 'depth', 'type': 'int'},
        'git_item_path': {'key': 'gitItemPath', 'type': 'str'},
        'is_non_conformant': {'key': 'isNonConformant', 'type': 'bool'},
        'is_parent_page': {'key': 'isParentPage', 'type': 'bool'},
        'order': {'key': 'order', 'type': 'int'},
        'path': {'key': 'path', 'type': 'str'}
    }

    def __init__(self, depth=None, git_item_path=None, is_non_conformant=None, is_parent_page=None, order=None, path=None):
        super(WikiPage, self).__init__()
        self.depth = depth
        self.git_item_path = git_item_path
        self.is_non_conformant = is_non_conformant
        self.is_parent_page = is_parent_page
        self.order = order
        self.path = path
