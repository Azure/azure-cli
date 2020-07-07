# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TfvcChangesetsRequestData(Model):
    """TfvcChangesetsRequestData.

    :param changeset_ids:
    :type changeset_ids: list of int
    :param comment_length:
    :type comment_length: int
    :param include_links: Whether to include the _links field on the shallow references
    :type include_links: bool
    """

    _attribute_map = {
        'changeset_ids': {'key': 'changesetIds', 'type': '[int]'},
        'comment_length': {'key': 'commentLength', 'type': 'int'},
        'include_links': {'key': 'includeLinks', 'type': 'bool'}
    }

    def __init__(self, changeset_ids=None, comment_length=None, include_links=None):
        super(TfvcChangesetsRequestData, self).__init__()
        self.changeset_ids = changeset_ids
        self.comment_length = comment_length
        self.include_links = include_links
