# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitStatusContext(Model):
    """GitStatusContext.

    :param genre: Genre of the status. Typically name of the service/tool generating the status, can be empty.
    :type genre: str
    :param name: Name identifier of the status, cannot be null or empty.
    :type name: str
    """

    _attribute_map = {
        'genre': {'key': 'genre', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, genre=None, name=None):
        super(GitStatusContext, self).__init__()
        self.genre = genre
        self.name = name
