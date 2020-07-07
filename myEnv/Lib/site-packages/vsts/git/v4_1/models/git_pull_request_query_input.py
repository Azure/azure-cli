# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitPullRequestQueryInput(Model):
    """GitPullRequestQueryInput.

    :param items: The list of commit IDs to search for.
    :type items: list of str
    :param type: The type of query to perform.
    :type type: object
    """

    _attribute_map = {
        'items': {'key': 'items', 'type': '[str]'},
        'type': {'key': 'type', 'type': 'object'}
    }

    def __init__(self, items=None, type=None):
        super(GitPullRequestQueryInput, self).__init__()
        self.items = items
        self.type = type
