# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .policy_type_ref import PolicyTypeRef


class PolicyType(PolicyTypeRef):
    """PolicyType.

    :param display_name: Display name of the policy type.
    :type display_name: str
    :param id: The policy type ID.
    :type id: str
    :param url: The URL where the policy type can be retrieved.
    :type url: str
    :param _links: The links to other objects related to this object.
    :type _links: :class:`ReferenceLinks <policy.v4_1.models.ReferenceLinks>`
    :param description: Detailed description of the policy type.
    :type description: str
    """

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'description': {'key': 'description', 'type': 'str'}
    }

    def __init__(self, display_name=None, id=None, url=None, _links=None, description=None):
        super(PolicyType, self).__init__(display_name=display_name, id=id, url=url)
        self._links = _links
        self.description = description
