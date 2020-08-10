# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PolicyConfigurationRef(Model):
    """PolicyConfigurationRef.

    :param id:
    :type id: int
    :param type:
    :type type: :class:`PolicyTypeRef <policy.v4_0.models.PolicyTypeRef>`
    :param url:
    :type url: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'type': {'key': 'type', 'type': 'PolicyTypeRef'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, id=None, type=None, url=None):
        super(PolicyConfigurationRef, self).__init__()
        self.id = id
        self.type = type
        self.url = url
