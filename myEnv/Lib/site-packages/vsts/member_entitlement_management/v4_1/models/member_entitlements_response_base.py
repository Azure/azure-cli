# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MemberEntitlementsResponseBase(Model):
    """MemberEntitlementsResponseBase.

    :param is_success: True if all operations were successful.
    :type is_success: bool
    :param member_entitlement: Result of the member entitlement after the operations. have been applied
    :type member_entitlement: :class:`MemberEntitlement <member-entitlement-management.v4_1.models.MemberEntitlement>`
    """

    _attribute_map = {
        'is_success': {'key': 'isSuccess', 'type': 'bool'},
        'member_entitlement': {'key': 'memberEntitlement', 'type': 'MemberEntitlement'}
    }

    def __init__(self, is_success=None, member_entitlement=None):
        super(MemberEntitlementsResponseBase, self).__init__()
        self.is_success = is_success
        self.member_entitlement = member_entitlement
