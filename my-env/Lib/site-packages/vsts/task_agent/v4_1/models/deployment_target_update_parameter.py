# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DeploymentTargetUpdateParameter(Model):
    """DeploymentTargetUpdateParameter.

    :param id: Identifier of the deployment target.
    :type id: int
    :param tags:
    :type tags: list of str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'tags': {'key': 'tags', 'type': '[str]'}
    }

    def __init__(self, id=None, tags=None):
        super(DeploymentTargetUpdateParameter, self).__init__()
        self.id = id
        self.tags = tags
