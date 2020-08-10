# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestIterationDetailsModel(Model):
    """TestIterationDetailsModel.

    :param action_results:
    :type action_results: list of :class:`TestActionResultModel <test.v4_0.models.TestActionResultModel>`
    :param attachments:
    :type attachments: list of :class:`TestCaseResultAttachmentModel <test.v4_0.models.TestCaseResultAttachmentModel>`
    :param comment:
    :type comment: str
    :param completed_date:
    :type completed_date: datetime
    :param duration_in_ms:
    :type duration_in_ms: float
    :param error_message:
    :type error_message: str
    :param id:
    :type id: int
    :param outcome:
    :type outcome: str
    :param parameters:
    :type parameters: list of :class:`TestResultParameterModel <test.v4_0.models.TestResultParameterModel>`
    :param started_date:
    :type started_date: datetime
    :param url:
    :type url: str
    """

    _attribute_map = {
        'action_results': {'key': 'actionResults', 'type': '[TestActionResultModel]'},
        'attachments': {'key': 'attachments', 'type': '[TestCaseResultAttachmentModel]'},
        'comment': {'key': 'comment', 'type': 'str'},
        'completed_date': {'key': 'completedDate', 'type': 'iso-8601'},
        'duration_in_ms': {'key': 'durationInMs', 'type': 'float'},
        'error_message': {'key': 'errorMessage', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'outcome': {'key': 'outcome', 'type': 'str'},
        'parameters': {'key': 'parameters', 'type': '[TestResultParameterModel]'},
        'started_date': {'key': 'startedDate', 'type': 'iso-8601'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, action_results=None, attachments=None, comment=None, completed_date=None, duration_in_ms=None, error_message=None, id=None, outcome=None, parameters=None, started_date=None, url=None):
        super(TestIterationDetailsModel, self).__init__()
        self.action_results = action_results
        self.attachments = attachments
        self.comment = comment
        self.completed_date = completed_date
        self.duration_in_ms = duration_in_ms
        self.error_message = error_message
        self.id = id
        self.outcome = outcome
        self.parameters = parameters
        self.started_date = started_date
        self.url = url
