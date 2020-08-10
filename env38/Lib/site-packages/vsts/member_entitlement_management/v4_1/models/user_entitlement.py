# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class UserEntitlement(Model):
    """UserEntitlement.

    :param access_level: User's access level denoted by a license.
    :type access_level: :class:`AccessLevel <member-entitlement-management.v4_1.models.AccessLevel>`
    :param extensions: User's extensions.
    :type extensions: list of :class:`Extension <member-entitlement-management.v4_1.models.Extension>`
    :param group_assignments: [Readonly] GroupEntitlements that this user belongs to.
    :type group_assignments: list of :class:`GroupEntitlement <member-entitlement-management.v4_1.models.GroupEntitlement>`
    :param id: The unique identifier which matches the Id of the Identity associated with the GraphMember.
    :type id: str
    :param last_accessed_date: [Readonly] Date the user last accessed the collection.
    :type last_accessed_date: datetime
    :param project_entitlements: Relation between a project and the user's effective permissions in that project.
    :type project_entitlements: list of :class:`ProjectEntitlement <member-entitlement-management.v4_1.models.ProjectEntitlement>`
    :param user: User reference.
    :type user: :class:`GraphUser <member-entitlement-management.v4_1.models.GraphUser>`
    """

    _attribute_map = {
        'access_level': {'key': 'accessLevel', 'type': 'AccessLevel'},
        'extensions': {'key': 'extensions', 'type': '[Extension]'},
        'group_assignments': {'key': 'groupAssignments', 'type': '[GroupEntitlement]'},
        'id': {'key': 'id', 'type': 'str'},
        'last_accessed_date': {'key': 'lastAccessedDate', 'type': 'iso-8601'},
        'project_entitlements': {'key': 'projectEntitlements', 'type': '[ProjectEntitlement]'},
        'user': {'key': 'user', 'type': 'GraphUser'}
    }

    def __init__(self, access_level=None, extensions=None, group_assignments=None, id=None, last_accessed_date=None, project_entitlements=None, user=None):
        super(UserEntitlement, self).__init__()
        self.access_level = access_level
        self.extensions = extensions
        self.group_assignments = group_assignments
        self.id = id
        self.last_accessed_date = last_accessed_date
        self.project_entitlements = project_entitlements
        self.user = user
