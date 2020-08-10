# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WikiAttachment(Model):
    """WikiAttachment.

    :param name: Name of the wiki attachment file.
    :type name: str
    :param path: Path of the wiki attachment file.
    :type path: str
    """

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'path': {'key': 'path', 'type': 'str'}
    }

    def __init__(self, name=None, path=None):
        super(WikiAttachment, self).__init__()
        self.name = name
        self.path = path
