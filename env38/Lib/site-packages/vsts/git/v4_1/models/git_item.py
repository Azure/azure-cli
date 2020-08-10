# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .item_model import ItemModel


class GitItem(ItemModel):
    """GitItem.

    :param _links:
    :type _links: :class:`ReferenceLinks <git.v4_1.models.ReferenceLinks>`
    :param content:
    :type content: str
    :param content_metadata:
    :type content_metadata: :class:`FileContentMetadata <git.v4_1.models.FileContentMetadata>`
    :param is_folder:
    :type is_folder: bool
    :param is_sym_link:
    :type is_sym_link: bool
    :param path:
    :type path: str
    :param url:
    :type url: str
    :param commit_id: SHA1 of commit item was fetched at
    :type commit_id: str
    :param git_object_type: Type of object (Commit, Tree, Blob, Tag, ...)
    :type git_object_type: object
    :param latest_processed_change: Shallow ref to commit that last changed this item Only populated if latestProcessedChange is requested May not be accurate if latest change is not yet cached
    :type latest_processed_change: :class:`GitCommitRef <git.v4_1.models.GitCommitRef>`
    :param object_id: Git object id
    :type object_id: str
    :param original_object_id: Git object id
    :type original_object_id: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'content': {'key': 'content', 'type': 'str'},
        'content_metadata': {'key': 'contentMetadata', 'type': 'FileContentMetadata'},
        'is_folder': {'key': 'isFolder', 'type': 'bool'},
        'is_sym_link': {'key': 'isSymLink', 'type': 'bool'},
        'path': {'key': 'path', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'commit_id': {'key': 'commitId', 'type': 'str'},
        'git_object_type': {'key': 'gitObjectType', 'type': 'object'},
        'latest_processed_change': {'key': 'latestProcessedChange', 'type': 'GitCommitRef'},
        'object_id': {'key': 'objectId', 'type': 'str'},
        'original_object_id': {'key': 'originalObjectId', 'type': 'str'}
    }

    def __init__(self, _links=None, content=None, content_metadata=None, is_folder=None, is_sym_link=None, path=None, url=None, commit_id=None, git_object_type=None, latest_processed_change=None, object_id=None, original_object_id=None):
        super(GitItem, self).__init__(_links=_links, content=content, content_metadata=content_metadata, is_folder=is_folder, is_sym_link=is_sym_link, path=path, url=url)
        self.commit_id = commit_id
        self.git_object_type = git_object_type
        self.latest_processed_change = latest_processed_change
        self.object_id = object_id
        self.original_object_id = original_object_id
