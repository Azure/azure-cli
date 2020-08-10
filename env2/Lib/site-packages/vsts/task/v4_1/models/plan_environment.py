# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PlanEnvironment(Model):
    """PlanEnvironment.

    :param mask:
    :type mask: list of :class:`MaskHint <task.v4_1.models.MaskHint>`
    :param options:
    :type options: dict
    :param variables:
    :type variables: dict
    """

    _attribute_map = {
        'mask': {'key': 'mask', 'type': '[MaskHint]'},
        'options': {'key': 'options', 'type': '{JobOption}'},
        'variables': {'key': 'variables', 'type': '{str}'}
    }

    def __init__(self, mask=None, options=None, variables=None):
        super(PlanEnvironment, self).__init__()
        self.mask = mask
        self.options = options
        self.variables = variables
