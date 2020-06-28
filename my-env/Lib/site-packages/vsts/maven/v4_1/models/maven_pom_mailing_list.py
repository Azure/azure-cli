# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MavenPomMailingList(Model):
    """MavenPomMailingList.

    :param archive:
    :type archive: str
    :param name:
    :type name: str
    :param other_archives:
    :type other_archives: list of str
    :param post:
    :type post: str
    :param subscribe:
    :type subscribe: str
    :param unsubscribe:
    :type unsubscribe: str
    """

    _attribute_map = {
        'archive': {'key': 'archive', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'other_archives': {'key': 'otherArchives', 'type': '[str]'},
        'post': {'key': 'post', 'type': 'str'},
        'subscribe': {'key': 'subscribe', 'type': 'str'},
        'unsubscribe': {'key': 'unsubscribe', 'type': 'str'}
    }

    def __init__(self, archive=None, name=None, other_archives=None, post=None, subscribe=None, unsubscribe=None):
        super(MavenPomMailingList, self).__init__()
        self.archive = archive
        self.name = name
        self.other_archives = other_archives
        self.post = post
        self.subscribe = subscribe
        self.unsubscribe = unsubscribe
