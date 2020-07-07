# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Member(Model):
    """Member.

    :param display_name:
    :type display_name: str
    :param id:
    :type id: str
    :param image_url:
    :type image_url: str
    :param unique_name:
    :type unique_name: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'display_name': {'key': 'displayName', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'image_url': {'key': 'imageUrl', 'type': 'str'},
        'unique_name': {'key': 'uniqueName', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, display_name=None, id=None, image_url=None, unique_name=None, url=None):
        super(Member, self).__init__()
        self.display_name = display_name
        self.id = id
        self.image_url = image_url
        self.unique_name = unique_name
        self.url = url
