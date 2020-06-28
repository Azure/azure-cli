# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResultModelBase(Model):
    """TestResultModelBase.

    :param comment:
    :type comment: str
    :param completed_date:
    :type completed_date: datetime
    :param duration_in_ms:
    :type duration_in_ms: float
    :param error_message:
    :type error_message: str
    :param outcome:
    :type outcome: str
    :param started_date:
    :type started_date: datetime
    """

    _attribute_map = {
        'comment': {'key': 'comment', 'type': 'str'},
        'completed_date': {'key': 'completedDate', 'type': 'iso-8601'},
        'duration_in_ms': {'key': 'durationInMs', 'type': 'float'},
        'error_message': {'key': 'errorMessage', 'type': 'str'},
        'outcome': {'key': 'outcome', 'type': 'str'},
        'started_date': {'key': 'startedDate', 'type': 'iso-8601'}
    }

    def __init__(self, comment=None, completed_date=None, duration_in_ms=None, error_message=None, outcome=None, started_date=None):
        super(TestResultModelBase, self).__init__()
        self.comment = comment
        self.completed_date = completed_date
        self.duration_in_ms = duration_in_ms
        self.error_message = error_message
        self.outcome = outcome
        self.started_date = started_date
