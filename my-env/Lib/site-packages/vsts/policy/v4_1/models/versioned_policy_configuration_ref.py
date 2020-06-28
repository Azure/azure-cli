# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .policy_configuration_ref import PolicyConfigurationRef


class VersionedPolicyConfigurationRef(PolicyConfigurationRef):
    """VersionedPolicyConfigurationRef.

    :param id: The policy configuration ID.
    :type id: int
    :param type: The policy configuration type.
    :type type: :class:`PolicyTypeRef <policy.v4_1.models.PolicyTypeRef>`
    :param url: The URL where the policy configuration can be retrieved.
    :type url: str
    :param revision: The policy configuration revision ID.
    :type revision: int
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'type': {'key': 'type', 'type': 'PolicyTypeRef'},
        'url': {'key': 'url', 'type': 'str'},
        'revision': {'key': 'revision', 'type': 'int'}
    }

    def __init__(self, id=None, type=None, url=None, revision=None):
        super(VersionedPolicyConfigurationRef, self).__init__(id=id, type=type, url=url)
        self.revision = revision
