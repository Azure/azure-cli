# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionBadge(Model):
    """ExtensionBadge.

    :param description:
    :type description: str
    :param img_uri:
    :type img_uri: str
    :param link:
    :type link: str
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'img_uri': {'key': 'imgUri', 'type': 'str'},
        'link': {'key': 'link', 'type': 'str'}
    }

    def __init__(self, description=None, img_uri=None, link=None):
        super(ExtensionBadge, self).__init__()
        self.description = description
        self.img_uri = img_uri
        self.link = link
