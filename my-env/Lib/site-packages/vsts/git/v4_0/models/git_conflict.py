# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitConflict(Model):
    """GitConflict.

    :param _links:
    :type _links: :class:`ReferenceLinks <git.v4_0.models.ReferenceLinks>`
    :param conflict_id:
    :type conflict_id: int
    :param conflict_path:
    :type conflict_path: str
    :param conflict_type:
    :type conflict_type: object
    :param merge_base_commit:
    :type merge_base_commit: :class:`GitCommitRef <git.v4_0.models.GitCommitRef>`
    :param merge_origin:
    :type merge_origin: :class:`GitMergeOriginRef <git.v4_0.models.GitMergeOriginRef>`
    :param merge_source_commit:
    :type merge_source_commit: :class:`GitCommitRef <git.v4_0.models.GitCommitRef>`
    :param merge_target_commit:
    :type merge_target_commit: :class:`GitCommitRef <git.v4_0.models.GitCommitRef>`
    :param resolution_error:
    :type resolution_error: object
    :param resolution_status:
    :type resolution_status: object
    :param resolved_by:
    :type resolved_by: :class:`IdentityRef <git.v4_0.models.IdentityRef>`
    :param resolved_date:
    :type resolved_date: datetime
    :param url:
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'conflict_id': {'key': 'conflictId', 'type': 'int'},
        'conflict_path': {'key': 'conflictPath', 'type': 'str'},
        'conflict_type': {'key': 'conflictType', 'type': 'object'},
        'merge_base_commit': {'key': 'mergeBaseCommit', 'type': 'GitCommitRef'},
        'merge_origin': {'key': 'mergeOrigin', 'type': 'GitMergeOriginRef'},
        'merge_source_commit': {'key': 'mergeSourceCommit', 'type': 'GitCommitRef'},
        'merge_target_commit': {'key': 'mergeTargetCommit', 'type': 'GitCommitRef'},
        'resolution_error': {'key': 'resolutionError', 'type': 'object'},
        'resolution_status': {'key': 'resolutionStatus', 'type': 'object'},
        'resolved_by': {'key': 'resolvedBy', 'type': 'IdentityRef'},
        'resolved_date': {'key': 'resolvedDate', 'type': 'iso-8601'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, conflict_id=None, conflict_path=None, conflict_type=None, merge_base_commit=None, merge_origin=None, merge_source_commit=None, merge_target_commit=None, resolution_error=None, resolution_status=None, resolved_by=None, resolved_date=None, url=None):
        super(GitConflict, self).__init__()
        self._links = _links
        self.conflict_id = conflict_id
        self.conflict_path = conflict_path
        self.conflict_type = conflict_type
        self.merge_base_commit = merge_base_commit
        self.merge_origin = merge_origin
        self.merge_source_commit = merge_source_commit
        self.merge_target_commit = merge_target_commit
        self.resolution_error = resolution_error
        self.resolution_status = resolution_status
        self.resolved_by = resolved_by
        self.resolved_date = resolved_date
        self.url = url
