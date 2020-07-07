# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class QueuedReleaseData(Model):
    """QueuedReleaseData.

    :param project_id:
    :type project_id: str
    :param queue_position:
    :type queue_position: int
    :param release_id:
    :type release_id: int
    """

    _attribute_map = {
        'project_id': {'key': 'projectId', 'type': 'str'},
        'queue_position': {'key': 'queuePosition', 'type': 'int'},
        'release_id': {'key': 'releaseId', 'type': 'int'}
    }

    def __init__(self, project_id=None, queue_position=None, release_id=None):
        super(QueuedReleaseData, self).__init__()
        self.project_id = project_id
        self.queue_position = queue_position
        self.release_id = release_id
