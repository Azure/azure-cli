# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResultParameterModel(Model):
    """TestResultParameterModel.

    :param action_path:
    :type action_path: str
    :param iteration_id:
    :type iteration_id: int
    :param parameter_name:
    :type parameter_name: str
    :param step_identifier: This is step Id of test case. For shared step, it is step Id of shared step in test case workitem; step Id in shared step. Example: TestCase workitem has two steps: 1) Normal step with Id = 1 2) Shared Step with Id = 2. Inside shared step: a) Normal Step with Id = 1 Value for StepIdentifier for First step: "1" Second step: "2;1"
    :type step_identifier: str
    :param url:
    :type url: str
    :param value:
    :type value: str
    """

    _attribute_map = {
        'action_path': {'key': 'actionPath', 'type': 'str'},
        'iteration_id': {'key': 'iterationId', 'type': 'int'},
        'parameter_name': {'key': 'parameterName', 'type': 'str'},
        'step_identifier': {'key': 'stepIdentifier', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'value': {'key': 'value', 'type': 'str'}
    }

    def __init__(self, action_path=None, iteration_id=None, parameter_name=None, step_identifier=None, url=None, value=None):
        super(TestResultParameterModel, self).__init__()
        self.action_path = action_path
        self.iteration_id = iteration_id
        self.parameter_name = parameter_name
        self.step_identifier = step_identifier
        self.url = url
        self.value = value
