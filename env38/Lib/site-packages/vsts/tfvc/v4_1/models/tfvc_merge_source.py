# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TfvcMergeSource(Model):
    """TfvcMergeSource.

    :param is_rename: Indicates if this a rename source. If false, it is a merge source.
    :type is_rename: bool
    :param server_item: The server item of the merge source
    :type server_item: str
    :param version_from: Start of the version range
    :type version_from: int
    :param version_to: End of the version range
    :type version_to: int
    """

    _attribute_map = {
        'is_rename': {'key': 'isRename', 'type': 'bool'},
        'server_item': {'key': 'serverItem', 'type': 'str'},
        'version_from': {'key': 'versionFrom', 'type': 'int'},
        'version_to': {'key': 'versionTo', 'type': 'int'}
    }

    def __init__(self, is_rename=None, server_item=None, version_from=None, version_to=None):
        super(TfvcMergeSource, self).__init__()
        self.is_rename = is_rename
        self.server_item = server_item
        self.version_from = version_from
        self.version_to = version_to
