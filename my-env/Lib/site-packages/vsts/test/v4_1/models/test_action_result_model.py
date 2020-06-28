# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .test_result_model_base import TestResultModelBase


class TestActionResultModel(TestResultModelBase):
    """TestActionResultModel.

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
    :param action_path:
    :type action_path: str
    :param iteration_id:
    :type iteration_id: int
    :param shared_step_model:
    :type shared_step_model: :class:`SharedStepModel <test.v4_1.models.SharedStepModel>`
    :param step_identifier: This is step Id of test case. For shared step, it is step Id of shared step in test case workitem; step Id in shared step. Example: TestCase workitem has two steps: 1) Normal step with Id = 1 2) Shared Step with Id = 2. Inside shared step: a) Normal Step with Id = 1 Value for StepIdentifier for First step: "1" Second step: "2;1"
    :type step_identifier: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'comment': {'key': 'comment', 'type': 'str'},
        'completed_date': {'key': 'completedDate', 'type': 'iso-8601'},
        'duration_in_ms': {'key': 'durationInMs', 'type': 'float'},
        'error_message': {'key': 'errorMessage', 'type': 'str'},
        'outcome': {'key': 'outcome', 'type': 'str'},
        'started_date': {'key': 'startedDate', 'type': 'iso-8601'},
        'action_path': {'key': 'actionPath', 'type': 'str'},
        'iteration_id': {'key': 'iterationId', 'type': 'int'},
        'shared_step_model': {'key': 'sharedStepModel', 'type': 'SharedStepModel'},
        'step_identifier': {'key': 'stepIdentifier', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, comment=None, completed_date=None, duration_in_ms=None, error_message=None, outcome=None, started_date=None, action_path=None, iteration_id=None, shared_step_model=None, step_identifier=None, url=None):
        super(TestActionResultModel, self).__init__(comment=comment, completed_date=completed_date, duration_in_ms=duration_in_ms, error_message=error_message, outcome=outcome, started_date=started_date)
        self.action_path = action_path
        self.iteration_id = iteration_id
        self.shared_step_model = shared_step_model
        self.step_identifier = step_identifier
        self.url = url
