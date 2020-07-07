# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AuthorizationGrant(Model):
    """AuthorizationGrant.

    :param grant_type:
    :type grant_type: object
    """

    _attribute_map = {
        'grant_type': {'key': 'grantType', 'type': 'object'}
    }

    def __init__(self, grant_type=None):
        super(AuthorizationGrant, self).__init__()
        self.grant_type = grant_type
