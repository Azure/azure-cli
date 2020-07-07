# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DeploymentGroupCreateParameterPoolProperty(Model):
    """DeploymentGroupCreateParameterPoolProperty.

    :param id: Deployment pool identifier.
    :type id: int
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'}
    }

    def __init__(self, id=None):
        super(DeploymentGroupCreateParameterPoolProperty, self).__init__()
        self.id = id
