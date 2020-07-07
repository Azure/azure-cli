# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .git_async_ref_operation import GitAsyncRefOperation


class GitRevert(GitAsyncRefOperation):
    """GitRevert.

    :param _links:
    :type _links: :class:`ReferenceLinks <git.v4_1.models.ReferenceLinks>`
    :param detailed_status:
    :type detailed_status: :class:`GitAsyncRefOperationDetail <git.v4_1.models.GitAsyncRefOperationDetail>`
    :param parameters:
    :type parameters: :class:`GitAsyncRefOperationParameters <git.v4_1.models.GitAsyncRefOperationParameters>`
    :param status:
    :type status: object
    :param url: A URL that can be used to make further requests for status about the operation
    :type url: str
    :param revert_id:
    :type revert_id: int
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'detailed_status': {'key': 'detailedStatus', 'type': 'GitAsyncRefOperationDetail'},
        'parameters': {'key': 'parameters', 'type': 'GitAsyncRefOperationParameters'},
        'status': {'key': 'status', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'},
        'revert_id': {'key': 'revertId', 'type': 'int'}
    }

    def __init__(self, _links=None, detailed_status=None, parameters=None, status=None, url=None, revert_id=None):
        super(GitRevert, self).__init__(_links=_links, detailed_status=detailed_status, parameters=parameters, status=status, url=url)
        self.revert_id = revert_id
