# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PagedGraphUsers(Model):
    """PagedGraphUsers.

    :param continuation_token: This will be non-null if there is another page of data. There will never be more than one continuation token returned by a request.
    :type continuation_token: list of str
    :param graph_users: The enumerable set of users found within a page.
    :type graph_users: list of :class:`GraphUser <graph.v4_1.models.GraphUser>`
    """

    _attribute_map = {
        'continuation_token': {'key': 'continuationToken', 'type': '[str]'},
        'graph_users': {'key': 'graphUsers', 'type': '[GraphUser]'}
    }

    def __init__(self, continuation_token=None, graph_users=None):
        super(PagedGraphUsers, self).__init__()
        self.continuation_token = continuation_token
        self.graph_users = graph_users
