# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class InputFilter(Model):
    """InputFilter.

    :param conditions: Groups of input filter expressions. This filter matches a set of inputs if any (one or more) of the groups evaluates to true.
    :type conditions: list of :class:`InputFilterCondition <microsoft.-visual-studio.-services.-web-api.v4_0.models.InputFilterCondition>`
    """

    _attribute_map = {
        'conditions': {'key': 'conditions', 'type': '[InputFilterCondition]'}
    }

    def __init__(self, conditions=None):
        super(InputFilter, self).__init__()
        self.conditions = conditions
