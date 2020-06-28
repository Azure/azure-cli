# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TimelineIterationStatus(Model):
    """TimelineIterationStatus.

    :param message:
    :type message: str
    :param type:
    :type type: object
    """

    _attribute_map = {
        'message': {'key': 'message', 'type': 'str'},
        'type': {'key': 'type', 'type': 'object'}
    }

    def __init__(self, message=None, type=None):
        super(TimelineIterationStatus, self).__init__()
        self.message = message
        self.type = type
