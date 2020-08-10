# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestRunMessage(Model):
    """TestRunMessage.

    :param agent_id:
    :type agent_id: str
    :param error_code:
    :type error_code: str
    :param logged_date:
    :type logged_date: datetime
    :param message:
    :type message: str
    :param message_id:
    :type message_id: str
    :param message_source:
    :type message_source: object
    :param message_type:
    :type message_type: object
    :param test_run_id:
    :type test_run_id: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'agent_id': {'key': 'agentId', 'type': 'str'},
        'error_code': {'key': 'errorCode', 'type': 'str'},
        'logged_date': {'key': 'loggedDate', 'type': 'iso-8601'},
        'message': {'key': 'message', 'type': 'str'},
        'message_id': {'key': 'messageId', 'type': 'str'},
        'message_source': {'key': 'messageSource', 'type': 'object'},
        'message_type': {'key': 'messageType', 'type': 'object'},
        'test_run_id': {'key': 'testRunId', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, agent_id=None, error_code=None, logged_date=None, message=None, message_id=None, message_source=None, message_type=None, test_run_id=None, url=None):
        super(TestRunMessage, self).__init__()
        self.agent_id = agent_id
        self.error_code = error_code
        self.logged_date = logged_date
        self.message = message
        self.message_id = message_id
        self.message_source = message_source
        self.message_type = message_type
        self.test_run_id = test_run_id
        self.url = url
