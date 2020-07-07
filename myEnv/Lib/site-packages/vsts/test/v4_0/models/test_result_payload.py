# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResultPayload(Model):
    """TestResultPayload.

    :param comment:
    :type comment: str
    :param name:
    :type name: str
    :param stream:
    :type stream: str
    """

    _attribute_map = {
        'comment': {'key': 'comment', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'stream': {'key': 'stream', 'type': 'str'}
    }

    def __init__(self, comment=None, name=None, stream=None):
        super(TestResultPayload, self).__init__()
        self.comment = comment
        self.name = name
        self.stream = stream
