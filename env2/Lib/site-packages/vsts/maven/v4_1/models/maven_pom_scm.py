# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MavenPomScm(Model):
    """MavenPomScm.

    :param connection:
    :type connection: str
    :param developer_connection:
    :type developer_connection: str
    :param tag:
    :type tag: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'connection': {'key': 'connection', 'type': 'str'},
        'developer_connection': {'key': 'developerConnection', 'type': 'str'},
        'tag': {'key': 'tag', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, connection=None, developer_connection=None, tag=None, url=None):
        super(MavenPomScm, self).__init__()
        self.connection = connection
        self.developer_connection = developer_connection
        self.tag = tag
        self.url = url
