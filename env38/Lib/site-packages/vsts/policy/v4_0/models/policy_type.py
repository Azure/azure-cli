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

    :param display_name:
    :type display_name: str
    :param id:
    :type id: str
    :param url:
    :type url: str
    :param _links:
    :type _links: :class:`ReferenceLinks <policy.v4_0.models.ReferenceLinks>`
    :param description:
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
