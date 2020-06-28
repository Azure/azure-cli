# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class HelpLink(Model):
    """HelpLink.

    :param text:
    :type text: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'text': {'key': 'text', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, text=None, url=None):
        super(HelpLink, self).__init__()
        self.text = text
        self.url = url
