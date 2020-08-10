# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemNextStateOnTransition(Model):
    """WorkItemNextStateOnTransition.

    :param error_code: Error code if there is no next state transition possible.
    :type error_code: str
    :param id: Work item ID.
    :type id: int
    :param message: Error message if there is no next state transition possible.
    :type message: str
    :param state_on_transition: Name of the next state on transition.
    :type state_on_transition: str
    """

    _attribute_map = {
        'error_code': {'key': 'errorCode', 'type': 'str'},
        'id': {'key': 'id', 'type': 'int'},
        'message': {'key': 'message', 'type': 'str'},
        'state_on_transition': {'key': 'stateOnTransition', 'type': 'str'}
    }

    def __init__(self, error_code=None, id=None, message=None, state_on_transition=None):
        super(WorkItemNextStateOnTransition, self).__init__()
        self.error_code = error_code
        self.id = id
        self.message = message
        self.state_on_transition = state_on_transition
