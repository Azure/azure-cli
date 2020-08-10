# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .identity_ref import IdentityRef


class IdentityRefWithVote(IdentityRef):
    """IdentityRefWithVote.

    :param directory_alias:
    :type directory_alias: str
    :param display_name:
    :type display_name: str
    :param id:
    :type id: str
    :param image_url:
    :type image_url: str
    :param inactive:
    :type inactive: bool
    :param is_aad_identity:
    :type is_aad_identity: bool
    :param is_container:
    :type is_container: bool
    :param profile_url:
    :type profile_url: str
    :param unique_name:
    :type unique_name: str
    :param url:
    :type url: str
    :param is_required:
    :type is_required: bool
    :param reviewer_url:
    :type reviewer_url: str
    :param vote:
    :type vote: int
    :param voted_for:
    :type voted_for: list of :class:`IdentityRefWithVote <git.v4_0.models.IdentityRefWithVote>`
    """

    _attribute_map = {
        'directory_alias': {'key': 'directoryAlias', 'type': 'str'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'image_url': {'key': 'imageUrl', 'type': 'str'},
        'inactive': {'key': 'inactive', 'type': 'bool'},
        'is_aad_identity': {'key': 'isAadIdentity', 'type': 'bool'},
        'is_container': {'key': 'isContainer', 'type': 'bool'},
        'profile_url': {'key': 'profileUrl', 'type': 'str'},
        'unique_name': {'key': 'uniqueName', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'is_required': {'key': 'isRequired', 'type': 'bool'},
        'reviewer_url': {'key': 'reviewerUrl', 'type': 'str'},
        'vote': {'key': 'vote', 'type': 'int'},
        'voted_for': {'key': 'votedFor', 'type': '[IdentityRefWithVote]'}
    }

    def __init__(self, directory_alias=None, display_name=None, id=None, image_url=None, inactive=None, is_aad_identity=None, is_container=None, profile_url=None, unique_name=None, url=None, is_required=None, reviewer_url=None, vote=None, voted_for=None):
        super(IdentityRefWithVote, self).__init__(directory_alias=directory_alias, display_name=display_name, id=id, image_url=image_url, inactive=inactive, is_aad_identity=is_aad_identity, is_container=is_container, profile_url=profile_url, unique_name=unique_name, url=url)
        self.is_required = is_required
        self.reviewer_url = reviewer_url
        self.vote = vote
        self.voted_for = voted_for
