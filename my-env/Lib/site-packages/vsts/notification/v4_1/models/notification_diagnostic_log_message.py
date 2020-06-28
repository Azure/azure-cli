# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationDiagnosticLogMessage(Model):
    """NotificationDiagnosticLogMessage.

    :param level: Corresponds to .Net TraceLevel enumeration
    :type level: int
    :param message:
    :type message: str
    :param time:
    :type time: object
    """

    _attribute_map = {
        'level': {'key': 'level', 'type': 'int'},
        'message': {'key': 'message', 'type': 'str'},
        'time': {'key': 'time', 'type': 'object'}
    }

    def __init__(self, level=None, message=None, time=None):
        super(NotificationDiagnosticLogMessage, self).__init__()
        self.level = level
        self.message = message
        self.time = time
