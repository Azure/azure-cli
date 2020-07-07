# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitPullRequestSearchCriteria(Model):
    """GitPullRequestSearchCriteria.

    :param creator_id: If set, search for pull requests that were created by this identity.
    :type creator_id: str
    :param include_links: Whether to include the _links field on the shallow references
    :type include_links: bool
    :param repository_id: If set, search for pull requests whose target branch is in this repository.
    :type repository_id: str
    :param reviewer_id: If set, search for pull requests that have this identity as a reviewer.
    :type reviewer_id: str
    :param source_ref_name: If set, search for pull requests from this branch.
    :type source_ref_name: str
    :param source_repository_id: If set, search for pull requests whose source branch is in this repository.
    :type source_repository_id: str
    :param status: If set, search for pull requests that are in this state.
    :type status: object
    :param target_ref_name: If set, search for pull requests into this branch.
    :type target_ref_name: str
    """

    _attribute_map = {
        'creator_id': {'key': 'creatorId', 'type': 'str'},
        'include_links': {'key': 'includeLinks', 'type': 'bool'},
        'repository_id': {'key': 'repositoryId', 'type': 'str'},
        'reviewer_id': {'key': 'reviewerId', 'type': 'str'},
        'source_ref_name': {'key': 'sourceRefName', 'type': 'str'},
        'source_repository_id': {'key': 'sourceRepositoryId', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'},
        'target_ref_name': {'key': 'targetRefName', 'type': 'str'}
    }

    def __init__(self, creator_id=None, include_links=None, repository_id=None, reviewer_id=None, source_ref_name=None, source_repository_id=None, status=None, target_ref_name=None):
        super(GitPullRequestSearchCriteria, self).__init__()
        self.creator_id = creator_id
        self.include_links = include_links
        self.repository_id = repository_id
        self.reviewer_id = reviewer_id
        self.source_ref_name = source_ref_name
        self.source_repository_id = source_repository_id
        self.status = status
        self.target_ref_name = target_ref_name
