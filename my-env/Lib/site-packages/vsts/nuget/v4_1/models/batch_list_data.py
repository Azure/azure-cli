# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .batch_operation_data import BatchOperationData


class BatchListData(BatchOperationData):
    """BatchListData.

    :param listed: The desired listed status for the package versions.
    :type listed: bool
    """

    _attribute_map = {
        'listed': {'key': 'listed', 'type': 'bool'}
    }

    def __init__(self, listed=None):
        super(BatchListData, self).__init__()
        self.listed = listed
