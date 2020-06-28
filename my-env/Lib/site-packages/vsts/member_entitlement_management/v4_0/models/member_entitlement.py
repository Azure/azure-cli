# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MemberEntitlement(Model):
    """MemberEntitlement.

    :param access_level: Member's access level denoted by a license
    :type access_level: :class:`AccessLevel <member-entitlement-management.v4_0.models.AccessLevel>`
    :param extensions: Member's extensions
    :type extensions: list of :class:`Extension <member-entitlement-management.v4_0.models.Extension>`
    :param group_assignments: GroupEntitlements that this member belongs to
    :type group_assignments: list of :class:`GroupEntitlement <member-entitlement-management.v4_0.models.GroupEntitlement>`
    :param id: The unique identifier which matches the Id of the GraphMember
    :type id: str
    :param last_accessed_date: Date the Member last access the collection
    :type last_accessed_date: datetime
    :param member: Member reference
    :type member: :class:`GraphMember <member-entitlement-management.v4_0.models.GraphMember>`
    :param project_entitlements: Relation between a project and the member's effective permissions in that project
    :type project_entitlements: list of :class:`ProjectEntitlement <member-entitlement-management.v4_0.models.ProjectEntitlement>`
    """

    _attribute_map = {
        'access_level': {'key': 'accessLevel', 'type': 'AccessLevel'},
        'extensions': {'key': 'extensions', 'type': '[Extension]'},
        'group_assignments': {'key': 'groupAssignments', 'type': '[GroupEntitlement]'},
        'id': {'key': 'id', 'type': 'str'},
        'last_accessed_date': {'key': 'lastAccessedDate', 'type': 'iso-8601'},
        'member': {'key': 'member', 'type': 'GraphMember'},
        'project_entitlements': {'key': 'projectEntitlements', 'type': '[ProjectEntitlement]'}
    }

    def __init__(self, access_level=None, extensions=None, group_assignments=None, id=None, last_accessed_date=None, member=None, project_entitlements=None):
        super(MemberEntitlement, self).__init__()
        self.access_level = access_level
        self.extensions = extensions
        self.group_assignments = group_assignments
        self.id = id
        self.last_accessed_date = last_accessed_date
        self.member = member
        self.project_entitlements = project_entitlements
