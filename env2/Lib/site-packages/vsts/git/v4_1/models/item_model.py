# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ItemModel(Model):
    """ItemModel.

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
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'content': {'key': 'content', 'type': 'str'},
        'content_metadata': {'key': 'contentMetadata', 'type': 'FileContentMetadata'},
        'is_folder': {'key': 'isFolder', 'type': 'bool'},
        'is_sym_link': {'key': 'isSymLink', 'type': 'bool'},
        'path': {'key': 'path', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, content=None, content_metadata=None, is_folder=None, is_sym_link=None, path=None, url=None):
        super(ItemModel, self).__init__()
        self._links = _links
        self.content = content
        self.content_metadata = content_metadata
        self.is_folder = is_folder
        self.is_sym_link = is_sym_link
        self.path = path
        self.url = url
