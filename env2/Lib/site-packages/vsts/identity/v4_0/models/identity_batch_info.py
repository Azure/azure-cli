# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class IdentityBatchInfo(Model):
    """IdentityBatchInfo.

    :param descriptors:
    :type descriptors: list of :class:`str <identities.v4_0.models.str>`
    :param identity_ids:
    :type identity_ids: list of str
    :param include_restricted_visibility:
    :type include_restricted_visibility: bool
    :param property_names:
    :type property_names: list of str
    :param query_membership:
    :type query_membership: object
    """

    _attribute_map = {
        'descriptors': {'key': 'descriptors', 'type': '[str]'},
        'identity_ids': {'key': 'identityIds', 'type': '[str]'},
        'include_restricted_visibility': {'key': 'includeRestrictedVisibility', 'type': 'bool'},
        'property_names': {'key': 'propertyNames', 'type': '[str]'},
        'query_membership': {'key': 'queryMembership', 'type': 'object'}
    }

    def __init__(self, descriptors=None, identity_ids=None, include_restricted_visibility=None, property_names=None, query_membership=None):
        super(IdentityBatchInfo, self).__init__()
        self.descriptors = descriptors
        self.identity_ids = identity_ids
        self.include_restricted_visibility = include_restricted_visibility
        self.property_names = property_names
        self.query_membership = query_membership
