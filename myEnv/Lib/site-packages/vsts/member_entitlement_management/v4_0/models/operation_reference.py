# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class OperationReference(Model):
    """OperationReference.

    :param id: The identifier for this operation.
    :type id: str
    :param status: The current status of the operation.
    :type status: object
    :param url: Url to get the full object.
    :type url: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, id=None, status=None, url=None):
        super(OperationReference, self).__init__()
        self.id = id
        self.status = status
        self.url = url
