# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitImportGitSource(Model):
    """GitImportGitSource.

    :param overwrite: Tells if this is a sync request or not
    :type overwrite: bool
    :param url: Url for the source repo
    :type url: str
    """

    _attribute_map = {
        'overwrite': {'key': 'overwrite', 'type': 'bool'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, overwrite=None, url=None):
        super(GitImportGitSource, self).__init__()
        self.overwrite = overwrite
        self.url = url
