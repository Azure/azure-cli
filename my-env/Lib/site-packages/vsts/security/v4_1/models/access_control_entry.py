# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccessControlEntry(Model):
    """AccessControlEntry.

    :param allow: The set of permission bits that represent the actions that the associated descriptor is allowed to perform.
    :type allow: int
    :param deny: The set of permission bits that represent the actions that the associated descriptor is not allowed to perform.
    :type deny: int
    :param descriptor: The descriptor for the user this AccessControlEntry applies to.
    :type descriptor: :class:`str <security.v4_1.models.str>`
    :param extended_info: This value, when set, reports the inherited and effective information for the associated descriptor. This value is only set on AccessControlEntries returned by the QueryAccessControlList(s) call when its includeExtendedInfo parameter is set to true.
    :type extended_info: :class:`AceExtendedInformation <security.v4_1.models.AceExtendedInformation>`
    """

    _attribute_map = {
        'allow': {'key': 'allow', 'type': 'int'},
        'deny': {'key': 'deny', 'type': 'int'},
        'descriptor': {'key': 'descriptor', 'type': 'str'},
        'extended_info': {'key': 'extendedInfo', 'type': 'AceExtendedInformation'}
    }

    def __init__(self, allow=None, deny=None, descriptor=None, extended_info=None):
        super(AccessControlEntry, self).__init__()
        self.allow = allow
        self.deny = deny
        self.descriptor = descriptor
        self.extended_info = extended_info
