# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .wiki_page_create_or_update_parameters import WikiPageCreateOrUpdateParameters


class WikiPage(WikiPageCreateOrUpdateParameters):
    """WikiPage.

    :param content: Content of the wiki page.
    :type content: str
    :param git_item_path: Path of the git item corresponding to the wiki page stored in the backing Git repository.
    :type git_item_path: str
    :param is_non_conformant: True if a page is non-conforming, i.e. 1) if the name doesn't match page naming standards. 2) if the page does not have a valid entry in the appropriate order file.
    :type is_non_conformant: bool
    :param is_parent_page: True if this page has subpages under its path.
    :type is_parent_page: bool
    :param order: Order of the wiki page, relative to other pages in the same hierarchy level.
    :type order: int
    :param path: Path of the wiki page.
    :type path: str
    :param remote_url: Remote web url to the wiki page.
    :type remote_url: str
    :param sub_pages: List of subpages of the current page.
    :type sub_pages: list of :class:`WikiPage <wiki.v4_1.models.WikiPage>`
    :param url: REST url for this wiki page.
    :type url: str
    """

    _attribute_map = {
        'content': {'key': 'content', 'type': 'str'},
        'git_item_path': {'key': 'gitItemPath', 'type': 'str'},
        'is_non_conformant': {'key': 'isNonConformant', 'type': 'bool'},
        'is_parent_page': {'key': 'isParentPage', 'type': 'bool'},
        'order': {'key': 'order', 'type': 'int'},
        'path': {'key': 'path', 'type': 'str'},
        'remote_url': {'key': 'remoteUrl', 'type': 'str'},
        'sub_pages': {'key': 'subPages', 'type': '[WikiPage]'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, content=None, git_item_path=None, is_non_conformant=None, is_parent_page=None, order=None, path=None, remote_url=None, sub_pages=None, url=None):
        super(WikiPage, self).__init__(content=content)
        self.git_item_path = git_item_path
        self.is_non_conformant = is_non_conformant
        self.is_parent_page = is_parent_page
        self.order = order
        self.path = path
        self.remote_url = remote_url
        self.sub_pages = sub_pages
        self.url = url
