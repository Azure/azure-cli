# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .item_model import ItemModel


class TfvcItem(ItemModel):
    """TfvcItem.

    :param _links:
    :type _links: :class:`ReferenceLinks <tfvc.v4_1.models.ReferenceLinks>`
    :param content:
    :type content: str
    :param content_metadata:
    :type content_metadata: :class:`FileContentMetadata <tfvc.v4_1.models.FileContentMetadata>`
    :param is_folder:
    :type is_folder: bool
    :param is_sym_link:
    :type is_sym_link: bool
    :param path:
    :type path: str
    :param url:
    :type url: str
    :param change_date:
    :type change_date: datetime
    :param deletion_id:
    :type deletion_id: int
    :param hash_value: MD5 hash as a base 64 string, applies to files only.
    :type hash_value: str
    :param is_branch:
    :type is_branch: bool
    :param is_pending_change:
    :type is_pending_change: bool
    :param size: The size of the file, if applicable.
    :type size: long
    :param version:
    :type version: int
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'content': {'key': 'content', 'type': 'str'},
        'content_metadata': {'key': 'contentMetadata', 'type': 'FileContentMetadata'},
        'is_folder': {'key': 'isFolder', 'type': 'bool'},
        'is_sym_link': {'key': 'isSymLink', 'type': 'bool'},
        'path': {'key': 'path', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'change_date': {'key': 'changeDate', 'type': 'iso-8601'},
        'deletion_id': {'key': 'deletionId', 'type': 'int'},
        'hash_value': {'key': 'hashValue', 'type': 'str'},
        'is_branch': {'key': 'isBranch', 'type': 'bool'},
        'is_pending_change': {'key': 'isPendingChange', 'type': 'bool'},
        'size': {'key': 'size', 'type': 'long'},
        'version': {'key': 'version', 'type': 'int'}
    }

    def __init__(self, _links=None, content=None, content_metadata=None, is_folder=None, is_sym_link=None, path=None, url=None, change_date=None, deletion_id=None, hash_value=None, is_branch=None, is_pending_change=None, size=None, version=None):
        super(TfvcItem, self).__init__(_links=_links, content=content, content_metadata=content_metadata, is_folder=is_folder, is_sym_link=is_sym_link, path=path, url=url)
        self.change_date = change_date
        self.deletion_id = deletion_id
        self.hash_value = hash_value
        self.is_branch = is_branch
        self.is_pending_change = is_pending_change
        self.size = size
        self.version = version
