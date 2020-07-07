# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .batch_operation_data import BatchOperationData


class BatchDeprecateData(BatchOperationData):
    """BatchDeprecateData.

    :param message: Deprecate message that will be added to packages
    :type message: str
    """

    _attribute_map = {
        'message': {'key': 'message', 'type': 'str'}
    }

    def __init__(self, message=None):
        super(BatchDeprecateData, self).__init__()
        self.message = message
