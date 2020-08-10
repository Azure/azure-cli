# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class OperationResultReference(Model):
    """OperationResultReference.

    :param result_url: URL to the operation result.
    :type result_url: str
    """

    _attribute_map = {
        'result_url': {'key': 'resultUrl', 'type': 'str'}
    }

    def __init__(self, result_url=None):
        super(OperationResultReference, self).__init__()
        self.result_url = result_url
