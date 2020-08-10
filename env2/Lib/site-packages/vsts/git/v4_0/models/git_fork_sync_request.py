# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitForkSyncRequest(Model):
    """GitForkSyncRequest.

    :param _links: Collection of related links
    :type _links: :class:`ReferenceLinks <git.v4_0.models.ReferenceLinks>`
    :param detailed_status:
    :type detailed_status: :class:`GitForkOperationStatusDetail <git.v4_0.models.GitForkOperationStatusDetail>`
    :param operation_id: Unique identifier for the operation.
    :type operation_id: int
    :param source: Fully-qualified identifier for the source repository.
    :type source: :class:`GlobalGitRepositoryKey <git.v4_0.models.GlobalGitRepositoryKey>`
    :param source_to_target_refs: If supplied, the set of ref mappings to use when performing a "sync" or create. If missing, all refs will be synchronized.
    :type source_to_target_refs: list of :class:`SourceToTargetRef <git.v4_0.models.SourceToTargetRef>`
    :param status:
    :type status: object
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'detailed_status': {'key': 'detailedStatus', 'type': 'GitForkOperationStatusDetail'},
        'operation_id': {'key': 'operationId', 'type': 'int'},
        'source': {'key': 'source', 'type': 'GlobalGitRepositoryKey'},
        'source_to_target_refs': {'key': 'sourceToTargetRefs', 'type': '[SourceToTargetRef]'},
        'status': {'key': 'status', 'type': 'object'}
    }

    def __init__(self, _links=None, detailed_status=None, operation_id=None, source=None, source_to_target_refs=None, status=None):
        super(GitForkSyncRequest, self).__init__()
        self._links = _links
        self.detailed_status = detailed_status
        self.operation_id = operation_id
        self.source = source
        self.source_to_target_refs = source_to_target_refs
        self.status = status
