# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .base_subscription_filter import BaseSubscriptionFilter


class ArtifactFilter(BaseSubscriptionFilter):
    """ArtifactFilter.

    :param event_type:
    :type event_type: str
    :param artifact_id:
    :type artifact_id: str
    :param artifact_type:
    :type artifact_type: str
    :param artifact_uri:
    :type artifact_uri: str
    :param type:
    :type type: str
    """

    _attribute_map = {
        'event_type': {'key': 'eventType', 'type': 'str'},
        'artifact_id': {'key': 'artifactId', 'type': 'str'},
        'artifact_type': {'key': 'artifactType', 'type': 'str'},
        'artifact_uri': {'key': 'artifactUri', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, event_type=None, artifact_id=None, artifact_type=None, artifact_uri=None, type=None):
        super(ArtifactFilter, self).__init__(event_type=event_type)
        self.artifact_id = artifact_id
        self.artifact_type = artifact_type
        self.artifact_uri = artifact_uri
        self.type = type
