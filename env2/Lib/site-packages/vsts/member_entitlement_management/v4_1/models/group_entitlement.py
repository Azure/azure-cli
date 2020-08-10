# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GroupEntitlement(Model):
    """GroupEntitlement.

    :param extension_rules: Extension Rules.
    :type extension_rules: list of :class:`Extension <member-entitlement-management.v4_1.models.Extension>`
    :param group: Member reference.
    :type group: :class:`GraphGroup <member-entitlement-management.v4_1.models.GraphGroup>`
    :param id: The unique identifier which matches the Id of the GraphMember.
    :type id: str
    :param last_executed: [Readonly] The last time the group licensing rule was executed (regardless of whether any changes were made).
    :type last_executed: datetime
    :param license_rule: License Rule.
    :type license_rule: :class:`AccessLevel <member-entitlement-management.v4_1.models.AccessLevel>`
    :param members: Group members. Only used when creating a new group.
    :type members: list of :class:`UserEntitlement <member-entitlement-management.v4_1.models.UserEntitlement>`
    :param project_entitlements: Relation between a project and the member's effective permissions in that project.
    :type project_entitlements: list of :class:`ProjectEntitlement <member-entitlement-management.v4_1.models.ProjectEntitlement>`
    :param status: The status of the group rule.
    :type status: object
    """

    _attribute_map = {
        'extension_rules': {'key': 'extensionRules', 'type': '[Extension]'},
        'group': {'key': 'group', 'type': 'GraphGroup'},
        'id': {'key': 'id', 'type': 'str'},
        'last_executed': {'key': 'lastExecuted', 'type': 'iso-8601'},
        'license_rule': {'key': 'licenseRule', 'type': 'AccessLevel'},
        'members': {'key': 'members', 'type': '[UserEntitlement]'},
        'project_entitlements': {'key': 'projectEntitlements', 'type': '[ProjectEntitlement]'},
        'status': {'key': 'status', 'type': 'object'}
    }

    def __init__(self, extension_rules=None, group=None, id=None, last_executed=None, license_rule=None, members=None, project_entitlements=None, status=None):
        super(GroupEntitlement, self).__init__()
        self.extension_rules = extension_rules
        self.group = group
        self.id = id
        self.last_executed = last_executed
        self.license_rule = license_rule
        self.members = members
        self.project_entitlements = project_entitlements
        self.status = status
