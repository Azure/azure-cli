# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitAsyncRefOperation(Model):
    """GitAsyncRefOperation.

    :param _links:
    :type _links: :class:`ReferenceLinks <git.v4_0.models.ReferenceLinks>`
    :param detailed_status:
    :type detailed_status: :class:`GitAsyncRefOperationDetail <git.v4_0.models.GitAsyncRefOperationDetail>`
    :param parameters:
    :type parameters: :class:`GitAsyncRefOperationParameters <git.v4_0.models.GitAsyncRefOperationParameters>`
    :param status:
    :type status: object
    :param url:
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'detailed_status': {'key': 'detailedStatus', 'type': 'GitAsyncRefOperationDetail'},
        'parameters': {'key': 'parameters', 'type': 'GitAsyncRefOperationParameters'},
        'status': {'key': 'status', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, detailed_status=None, parameters=None, status=None, url=None):
        super(GitAsyncRefOperation, self).__init__()
        self._links = _links
        self.detailed_status = detailed_status
        self.parameters = parameters
        self.status = status
        self.url = url
