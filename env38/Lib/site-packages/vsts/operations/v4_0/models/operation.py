# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .operation_reference import OperationReference


class Operation(OperationReference):
    """Operation.

    :param id: The identifier for this operation.
    :type id: str
    :param status: The current status of the operation.
    :type status: object
    :param url: Url to get the full object.
    :type url: str
    :param _links: The links to other objects related to this object.
    :type _links: :class:`ReferenceLinks <operations.v4_0.models.ReferenceLinks>`
    :param result_message: The result message which is generally not set.
    :type result_message: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'result_message': {'key': 'resultMessage', 'type': 'str'}
    }

    def __init__(self, id=None, status=None, url=None, _links=None, result_message=None):
        super(Operation, self).__init__(id=id, status=status, url=url)
        self._links = _links
        self.result_message = result_message
