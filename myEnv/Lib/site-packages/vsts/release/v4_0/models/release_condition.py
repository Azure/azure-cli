# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .condition import Condition


class ReleaseCondition(Condition):
    """ReleaseCondition.

    :param condition_type:
    :type condition_type: object
    :param name:
    :type name: str
    :param value:
    :type value: str
    :param result:
    :type result: bool
    """

    _attribute_map = {
        'condition_type': {'key': 'conditionType', 'type': 'object'},
        'name': {'key': 'name', 'type': 'str'},
        'value': {'key': 'value', 'type': 'str'},
        'result': {'key': 'result', 'type': 'bool'}
    }

    def __init__(self, condition_type=None, name=None, value=None, result=None):
        super(ReleaseCondition, self).__init__(condition_type=condition_type, name=name, value=value)
        self.result = result
