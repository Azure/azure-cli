# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ClientTraceEvent(Model):
    """ClientTraceEvent.

    :param area:
    :type area: str
    :param component:
    :type component: str
    :param exception_type:
    :type exception_type: str
    :param feature:
    :type feature: str
    :param level:
    :type level: object
    :param message:
    :type message: str
    :param method:
    :type method: str
    :param properties:
    :type properties: dict
    """

    _attribute_map = {
        'area': {'key': 'area', 'type': 'str'},
        'component': {'key': 'component', 'type': 'str'},
        'exception_type': {'key': 'exceptionType', 'type': 'str'},
        'feature': {'key': 'feature', 'type': 'str'},
        'level': {'key': 'level', 'type': 'object'},
        'message': {'key': 'message', 'type': 'str'},
        'method': {'key': 'method', 'type': 'str'},
        'properties': {'key': 'properties', 'type': '{object}'}
    }

    def __init__(self, area=None, component=None, exception_type=None, feature=None, level=None, message=None, method=None, properties=None):
        super(ClientTraceEvent, self).__init__()
        self.area = area
        self.component = component
        self.exception_type = exception_type
        self.feature = feature
        self.level = level
        self.message = message
        self.method = method
        self.properties = properties
