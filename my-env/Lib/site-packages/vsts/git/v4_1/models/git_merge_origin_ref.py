# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitMergeOriginRef(Model):
    """GitMergeOriginRef.

    :param pull_request_id:
    :type pull_request_id: int
    """

    _attribute_map = {
        'pull_request_id': {'key': 'pullRequestId', 'type': 'int'}
    }

    def __init__(self, pull_request_id=None):
        super(GitMergeOriginRef, self).__init__()
        self.pull_request_id = pull_request_id
