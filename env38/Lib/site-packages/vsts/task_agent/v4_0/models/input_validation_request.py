# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class InputValidationRequest(Model):
    """InputValidationRequest.

    :param inputs:
    :type inputs: dict
    """

    _attribute_map = {
        'inputs': {'key': 'inputs', 'type': '{ValidationItem}'}
    }

    def __init__(self, inputs=None):
        super(InputValidationRequest, self).__init__()
        self.inputs = inputs
