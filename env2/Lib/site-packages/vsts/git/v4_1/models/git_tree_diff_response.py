# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitTreeDiffResponse(Model):
    """GitTreeDiffResponse.

    :param continuation_token: The HTTP client methods find the continuation token header in the response and populate this field.
    :type continuation_token: list of str
    :param tree_diff:
    :type tree_diff: :class:`GitTreeDiff <git.v4_1.models.GitTreeDiff>`
    """

    _attribute_map = {
        'continuation_token': {'key': 'continuationToken', 'type': '[str]'},
        'tree_diff': {'key': 'treeDiff', 'type': 'GitTreeDiff'}
    }

    def __init__(self, continuation_token=None, tree_diff=None):
        super(GitTreeDiffResponse, self).__init__()
        self.continuation_token = continuation_token
        self.tree_diff = tree_diff
