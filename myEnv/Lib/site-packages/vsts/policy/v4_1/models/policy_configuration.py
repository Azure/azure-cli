# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .versioned_policy_configuration_ref import VersionedPolicyConfigurationRef


class PolicyConfiguration(VersionedPolicyConfigurationRef):
    """PolicyConfiguration.

    :param id: The policy configuration ID.
    :type id: int
    :param type: The policy configuration type.
    :type type: :class:`PolicyTypeRef <policy.v4_1.models.PolicyTypeRef>`
    :param url: The URL where the policy configuration can be retrieved.
    :type url: str
    :param revision: The policy configuration revision ID.
    :type revision: int
    :param _links: The links to other objects related to this object.
    :type _links: :class:`ReferenceLinks <policy.v4_1.models.ReferenceLinks>`
    :param created_by: A reference to the identity that created the policy.
    :type created_by: :class:`IdentityRef <policy.v4_1.models.IdentityRef>`
    :param created_date: The date and time when the policy was created.
    :type created_date: datetime
    :param is_blocking: Indicates whether the policy is blocking.
    :type is_blocking: bool
    :param is_deleted: Indicates whether the policy has been (soft) deleted.
    :type is_deleted: bool
    :param is_enabled: Indicates whether the policy is enabled.
    :type is_enabled: bool
    :param settings: The policy configuration settings.
    :type settings: :class:`object <policy.v4_1.models.object>`
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'type': {'key': 'type', 'type': 'PolicyTypeRef'},
        'url': {'key': 'url', 'type': 'str'},
        'revision': {'key': 'revision', 'type': 'int'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'is_blocking': {'key': 'isBlocking', 'type': 'bool'},
        'is_deleted': {'key': 'isDeleted', 'type': 'bool'},
        'is_enabled': {'key': 'isEnabled', 'type': 'bool'},
        'settings': {'key': 'settings', 'type': 'object'}
    }

    def __init__(self, id=None, type=None, url=None, revision=None, _links=None, created_by=None, created_date=None, is_blocking=None, is_deleted=None, is_enabled=None, settings=None):
        super(PolicyConfiguration, self).__init__(id=id, type=type, url=url, revision=revision)
        self._links = _links
        self.created_by = created_by
        self.created_date = created_date
        self.is_blocking = is_blocking
        self.is_deleted = is_deleted
        self.is_enabled = is_enabled
        self.settings = settings
