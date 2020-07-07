# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitTreeEntryRef(Model):
    """GitTreeEntryRef.

    :param git_object_type: Blob or tree
    :type git_object_type: object
    :param mode: Mode represented as octal string
    :type mode: str
    :param object_id: SHA1 hash of git object
    :type object_id: str
    :param relative_path: Path relative to parent tree object
    :type relative_path: str
    :param size: Size of content
    :type size: long
    :param url: url to retrieve tree or blob
    :type url: str
    """

    _attribute_map = {
        'git_object_type': {'key': 'gitObjectType', 'type': 'object'},
        'mode': {'key': 'mode', 'type': 'str'},
        'object_id': {'key': 'objectId', 'type': 'str'},
        'relative_path': {'key': 'relativePath', 'type': 'str'},
        'size': {'key': 'size', 'type': 'long'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, git_object_type=None, mode=None, object_id=None, relative_path=None, size=None, url=None):
        super(GitTreeEntryRef, self).__init__()
        self.git_object_type = git_object_type
        self.mode = mode
        self.object_id = object_id
        self.relative_path = relative_path
        self.size = size
        self.url = url
