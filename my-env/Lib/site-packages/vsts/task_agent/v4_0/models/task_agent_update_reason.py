# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentUpdateReason(Model):
    """TaskAgentUpdateReason.

    :param code:
    :type code: object
    """

    _attribute_map = {
        'code': {'key': 'code', 'type': 'object'}
    }

    def __init__(self, code=None):
        super(TaskAgentUpdateReason, self).__init__()
        self.code = code
