# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AceExtendedInformation(Model):
    """AceExtendedInformation.

    :param effective_allow: This is the combination of all of the explicit and inherited permissions for this identity on this token.  These are the permissions used when determining if a given user has permission to perform an action.
    :type effective_allow: int
    :param effective_deny: This is the combination of all of the explicit and inherited permissions for this identity on this token.  These are the permissions used when determining if a given user has permission to perform an action.
    :type effective_deny: int
    :param inherited_allow: These are the permissions that are inherited for this identity on this token.  If the token does not inherit permissions this will be 0.  Note that any permissions that have been explicitly set on this token for this identity, or any groups that this identity is a part of, are not included here.
    :type inherited_allow: int
    :param inherited_deny: These are the permissions that are inherited for this identity on this token.  If the token does not inherit permissions this will be 0.  Note that any permissions that have been explicitly set on this token for this identity, or any groups that this identity is a part of, are not included here.
    :type inherited_deny: int
    """

    _attribute_map = {
        'effective_allow': {'key': 'effectiveAllow', 'type': 'int'},
        'effective_deny': {'key': 'effectiveDeny', 'type': 'int'},
        'inherited_allow': {'key': 'inheritedAllow', 'type': 'int'},
        'inherited_deny': {'key': 'inheritedDeny', 'type': 'int'}
    }

    def __init__(self, effective_allow=None, effective_deny=None, inherited_allow=None, inherited_deny=None):
        super(AceExtendedInformation, self).__init__()
        self.effective_allow = effective_allow
        self.effective_deny = effective_deny
        self.inherited_allow = inherited_allow
        self.inherited_deny = inherited_deny
