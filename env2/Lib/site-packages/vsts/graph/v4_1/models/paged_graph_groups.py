# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PagedGraphGroups(Model):
    """PagedGraphGroups.

    :param continuation_token: This will be non-null if there is another page of data. There will never be more than one continuation token returned by a request.
    :type continuation_token: list of str
    :param graph_groups: The enumerable list of groups found within a page.
    :type graph_groups: list of :class:`GraphGroup <graph.v4_1.models.GraphGroup>`
    """

    _attribute_map = {
        'continuation_token': {'key': 'continuationToken', 'type': '[str]'},
        'graph_groups': {'key': 'graphGroups', 'type': '[GraphGroup]'}
    }

    def __init__(self, continuation_token=None, graph_groups=None):
        super(PagedGraphGroups, self).__init__()
        self.continuation_token = continuation_token
        self.graph_groups = graph_groups
