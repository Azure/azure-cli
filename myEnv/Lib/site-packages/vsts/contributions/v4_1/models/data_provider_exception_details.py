# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DataProviderExceptionDetails(Model):
    """DataProviderExceptionDetails.

    :param exception_type: The type of the exception that was thrown.
    :type exception_type: str
    :param message: Message that is associated with the exception.
    :type message: str
    :param stack_trace: The StackTrace from the exception turned into a string.
    :type stack_trace: str
    """

    _attribute_map = {
        'exception_type': {'key': 'exceptionType', 'type': 'str'},
        'message': {'key': 'message', 'type': 'str'},
        'stack_trace': {'key': 'stackTrace', 'type': 'str'}
    }

    def __init__(self, exception_type=None, message=None, stack_trace=None):
        super(DataProviderExceptionDetails, self).__init__()
        self.exception_type = exception_type
        self.message = message
        self.stack_trace = stack_trace
