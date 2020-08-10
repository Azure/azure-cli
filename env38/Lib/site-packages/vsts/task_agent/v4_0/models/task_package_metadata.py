# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskPackageMetadata(Model):
    """TaskPackageMetadata.

    :param type: Gets the name of the package.
    :type type: str
    :param url: Gets the url of the package.
    :type url: str
    :param version: Gets the version of the package.
    :type version: str
    """

    _attribute_map = {
        'type': {'key': 'type', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, type=None, url=None, version=None):
        super(TaskPackageMetadata, self).__init__()
        self.type = type
        self.url = url
        self.version = version
