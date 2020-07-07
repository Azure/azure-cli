# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PolicyTypeRef(Model):
    """PolicyTypeRef.

    :param display_name:
    :type display_name: str
    :param id:
    :type id: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, display_name=None, id=None, url=None):
        super(PolicyTypeRef, self).__init__()
        self.display_name = display_name
        self.id = id
        self.url = url
