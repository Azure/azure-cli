# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class INotificationDiagnosticLog(Model):
    """INotificationDiagnosticLog.

    :param activity_id:
    :type activity_id: str
    :param description:
    :type description: str
    :param end_time:
    :type end_time: datetime
    :param id:
    :type id: str
    :param log_type:
    :type log_type: str
    :param messages:
    :type messages: list of :class:`NotificationDiagnosticLogMessage <notification.v4_1.models.NotificationDiagnosticLogMessage>`
    :param properties:
    :type properties: dict
    :param source:
    :type source: str
    :param start_time:
    :type start_time: datetime
    """

    _attribute_map = {
        'activity_id': {'key': 'activityId', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'end_time': {'key': 'endTime', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'str'},
        'log_type': {'key': 'logType', 'type': 'str'},
        'messages': {'key': 'messages', 'type': '[NotificationDiagnosticLogMessage]'},
        'properties': {'key': 'properties', 'type': '{str}'},
        'source': {'key': 'source', 'type': 'str'},
        'start_time': {'key': 'startTime', 'type': 'iso-8601'}
    }

    def __init__(self, activity_id=None, description=None, end_time=None, id=None, log_type=None, messages=None, properties=None, source=None, start_time=None):
        super(INotificationDiagnosticLog, self).__init__()
        self.activity_id = activity_id
        self.description = description
        self.end_time = end_time
        self.id = id
        self.log_type = log_type
        self.messages = messages
        self.properties = properties
        self.source = source
        self.start_time = start_time
