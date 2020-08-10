# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class IdentitySnapshot(Model):
    """IdentitySnapshot.

    :param groups:
    :type groups: list of :class:`Identity <identities.v4_1.models.Identity>`
    :param identity_ids:
    :type identity_ids: list of str
    :param memberships:
    :type memberships: list of :class:`GroupMembership <identities.v4_1.models.GroupMembership>`
    :param scope_id:
    :type scope_id: str
    :param scopes:
    :type scopes: list of :class:`IdentityScope <identities.v4_1.models.IdentityScope>`
    """

    _attribute_map = {
        'groups': {'key': 'groups', 'type': '[Identity]'},
        'identity_ids': {'key': 'identityIds', 'type': '[str]'},
        'memberships': {'key': 'memberships', 'type': '[GroupMembership]'},
        'scope_id': {'key': 'scopeId', 'type': 'str'},
        'scopes': {'key': 'scopes', 'type': '[IdentityScope]'}
    }

    def __init__(self, groups=None, identity_ids=None, memberships=None, scope_id=None, scopes=None):
        super(IdentitySnapshot, self).__init__()
        self.groups = groups
        self.identity_ids = identity_ids
        self.memberships = memberships
        self.scope_id = scope_id
        self.scopes = scopes
