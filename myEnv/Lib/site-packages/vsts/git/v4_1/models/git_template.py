# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitTemplate(Model):
    """GitTemplate.

    :param name: Name of the Template
    :type name: str
    :param type: Type of the Template
    :type type: str
    """

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, name=None, type=None):
        super(GitTemplate, self).__init__()
        self.name = name
        self.type = type
