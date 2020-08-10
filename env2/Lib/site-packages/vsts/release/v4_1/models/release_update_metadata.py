# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseUpdateMetadata(Model):
    """ReleaseUpdateMetadata.

    :param comment: Sets comment for release.
    :type comment: str
    :param keep_forever: Set 'true' to exclude the release from retention policies.
    :type keep_forever: bool
    :param manual_environments: Sets list of manual environments.
    :type manual_environments: list of str
    :param status: Sets status of the release.
    :type status: object
    """

    _attribute_map = {
        'comment': {'key': 'comment', 'type': 'str'},
        'keep_forever': {'key': 'keepForever', 'type': 'bool'},
        'manual_environments': {'key': 'manualEnvironments', 'type': '[str]'},
        'status': {'key': 'status', 'type': 'object'}
    }

    def __init__(self, comment=None, keep_forever=None, manual_environments=None, status=None):
        super(ReleaseUpdateMetadata, self).__init__()
        self.comment = comment
        self.keep_forever = keep_forever
        self.manual_environments = manual_environments
        self.status = status
