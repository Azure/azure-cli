# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseEnvironmentUpdateMetadata(Model):
    """ReleaseEnvironmentUpdateMetadata.

    :param comment: Gets or sets comment.
    :type comment: str
    :param scheduled_deployment_time: Gets or sets scheduled deployment time.
    :type scheduled_deployment_time: datetime
    :param status: Gets or sets status of environment.
    :type status: object
    """

    _attribute_map = {
        'comment': {'key': 'comment', 'type': 'str'},
        'scheduled_deployment_time': {'key': 'scheduledDeploymentTime', 'type': 'iso-8601'},
        'status': {'key': 'status', 'type': 'object'}
    }

    def __init__(self, comment=None, scheduled_deployment_time=None, status=None):
        super(ReleaseEnvironmentUpdateMetadata, self).__init__()
        self.comment = comment
        self.scheduled_deployment_time = scheduled_deployment_time
        self.status = status
