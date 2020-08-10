# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitForkOperationStatusDetail(Model):
    """GitForkOperationStatusDetail.

    :param all_steps: All valid steps for the forking process
    :type all_steps: list of str
    :param current_step: Index into AllSteps for the current step
    :type current_step: int
    :param error_message: Error message if the operation failed.
    :type error_message: str
    """

    _attribute_map = {
        'all_steps': {'key': 'allSteps', 'type': '[str]'},
        'current_step': {'key': 'currentStep', 'type': 'int'},
        'error_message': {'key': 'errorMessage', 'type': 'str'}
    }

    def __init__(self, all_steps=None, current_step=None, error_message=None):
        super(GitForkOperationStatusDetail, self).__init__()
        self.all_steps = all_steps
        self.current_step = current_step
        self.error_message = error_message
