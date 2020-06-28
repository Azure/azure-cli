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

    :param extension_rules: Extension Rules
    :type extension_rules: list of :class:`Extension <member-entitlement-management.v4_0.models.Extension>`
    :param group: Member reference
    :type group: :class:`GraphGroup <member-entitlement-management.v4_0.models.GraphGroup>`
    :param id: The unique identifier which matches the Id of the GraphMember
    :type id: str
    :param license_rule: License Rule
    :type license_rule: :class:`AccessLevel <member-entitlement-management.v4_0.models.AccessLevel>`
    :param project_entitlements: Relation between a project and the member's effective permissions in that project
    :type project_entitlements: list of :class:`ProjectEntitlement <member-entitlement-management.v4_0.models.ProjectEntitlement>`
    :param status:
    :type status: object
    """

    _attribute_map = {
        'extension_rules': {'key': 'extensionRules', 'type': '[Extension]'},
        'group': {'key': 'group', 'type': 'GraphGroup'},
        'id': {'key': 'id', 'type': 'str'},
        'license_rule': {'key': 'licenseRule', 'type': 'AccessLevel'},
        'project_entitlements': {'key': 'projectEntitlements', 'type': '[ProjectEntitlement]'},
        'status': {'key': 'status', 'type': 'object'}
    }

    def __init__(self, extension_rules=None, group=None, id=None, license_rule=None, project_entitlements=None, status=None):
        super(GroupEntitlement, self).__init__()
        self.extension_rules = extension_rules
        self.group = group
        self.id = id
        self.license_rule = license_rule
        self.project_entitlements = project_entitlements
        self.status = status
