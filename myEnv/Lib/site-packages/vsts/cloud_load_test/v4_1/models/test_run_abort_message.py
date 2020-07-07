# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestRunAbortMessage(Model):
    """TestRunAbortMessage.

    :param action:
    :type action: str
    :param cause:
    :type cause: str
    :param details:
    :type details: list of str
    :param logged_date:
    :type logged_date: datetime
    :param source:
    :type source: str
    """

    _attribute_map = {
        'action': {'key': 'action', 'type': 'str'},
        'cause': {'key': 'cause', 'type': 'str'},
        'details': {'key': 'details', 'type': '[str]'},
        'logged_date': {'key': 'loggedDate', 'type': 'iso-8601'},
        'source': {'key': 'source', 'type': 'str'}
    }

    def __init__(self, action=None, cause=None, details=None, logged_date=None, source=None):
        super(TestRunAbortMessage, self).__init__()
        self.action = action
        self.cause = cause
        self.details = details
        self.logged_date = logged_date
        self.source = source
