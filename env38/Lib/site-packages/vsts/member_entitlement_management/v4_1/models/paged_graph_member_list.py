# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PagedGraphMemberList(Model):
    """PagedGraphMemberList.

    :param continuation_token:
    :type continuation_token: str
    :param members:
    :type members: list of :class:`UserEntitlement <member-entitlement-management.v4_1.models.UserEntitlement>`
    """

    _attribute_map = {
        'continuation_token': {'key': 'continuationToken', 'type': 'str'},
        'members': {'key': 'members', 'type': '[UserEntitlement]'}
    }

    def __init__(self, continuation_token=None, members=None):
        super(PagedGraphMemberList, self).__init__()
        self.continuation_token = continuation_token
        self.members = members
