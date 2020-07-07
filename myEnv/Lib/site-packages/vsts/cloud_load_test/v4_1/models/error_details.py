# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ErrorDetails(Model):
    """ErrorDetails.

    :param last_error_date:
    :type last_error_date: datetime
    :param message_text:
    :type message_text: str
    :param occurrences:
    :type occurrences: int
    :param request:
    :type request: str
    :param scenario_name:
    :type scenario_name: str
    :param stack_trace:
    :type stack_trace: str
    :param test_case_name:
    :type test_case_name: str
    """

    _attribute_map = {
        'last_error_date': {'key': 'lastErrorDate', 'type': 'iso-8601'},
        'message_text': {'key': 'messageText', 'type': 'str'},
        'occurrences': {'key': 'occurrences', 'type': 'int'},
        'request': {'key': 'request', 'type': 'str'},
        'scenario_name': {'key': 'scenarioName', 'type': 'str'},
        'stack_trace': {'key': 'stackTrace', 'type': 'str'},
        'test_case_name': {'key': 'testCaseName', 'type': 'str'}
    }

    def __init__(self, last_error_date=None, message_text=None, occurrences=None, request=None, scenario_name=None, stack_trace=None, test_case_name=None):
        super(ErrorDetails, self).__init__()
        self.last_error_date = last_error_date
        self.message_text = message_text
        self.occurrences = occurrences
        self.request = request
        self.scenario_name = scenario_name
        self.stack_trace = stack_trace
        self.test_case_name = test_case_name
