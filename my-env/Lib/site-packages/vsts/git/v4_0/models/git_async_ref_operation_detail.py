# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitAsyncRefOperationDetail(Model):
    """GitAsyncRefOperationDetail.

    :param conflict:
    :type conflict: bool
    :param current_commit_id:
    :type current_commit_id: str
    :param failure_message:
    :type failure_message: str
    :param progress:
    :type progress: float
    :param status:
    :type status: object
    :param timedout:
    :type timedout: bool
    """

    _attribute_map = {
        'conflict': {'key': 'conflict', 'type': 'bool'},
        'current_commit_id': {'key': 'currentCommitId', 'type': 'str'},
        'failure_message': {'key': 'failureMessage', 'type': 'str'},
        'progress': {'key': 'progress', 'type': 'float'},
        'status': {'key': 'status', 'type': 'object'},
        'timedout': {'key': 'timedout', 'type': 'bool'}
    }

    def __init__(self, conflict=None, current_commit_id=None, failure_message=None, progress=None, status=None, timedout=None):
        super(GitAsyncRefOperationDetail, self).__init__()
        self.conflict = conflict
        self.current_commit_id = current_commit_id
        self.failure_message = failure_message
        self.progress = progress
        self.status = status
        self.timedout = timedout
