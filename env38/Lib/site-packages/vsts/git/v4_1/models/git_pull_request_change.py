# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitPullRequestChange(Model):
    """GitPullRequestChange.

    :param change_tracking_id: ID used to track files through multiple changes.
    :type change_tracking_id: int
    """

    _attribute_map = {
        'change_tracking_id': {'key': 'changeTrackingId', 'type': 'int'}
    }

    def __init__(self, change_tracking_id=None):
        super(GitPullRequestChange, self).__init__()
        self.change_tracking_id = change_tracking_id
