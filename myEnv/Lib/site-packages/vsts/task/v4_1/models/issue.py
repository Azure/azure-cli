# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Issue(Model):
    """Issue.

    :param category:
    :type category: str
    :param data:
    :type data: dict
    :param message:
    :type message: str
    :param type:
    :type type: object
    """

    _attribute_map = {
        'category': {'key': 'category', 'type': 'str'},
        'data': {'key': 'data', 'type': '{str}'},
        'message': {'key': 'message', 'type': 'str'},
        'type': {'key': 'type', 'type': 'object'}
    }

    def __init__(self, category=None, data=None, message=None, type=None):
        super(Issue, self).__init__()
        self.category = category
        self.data = data
        self.message = message
        self.type = type
