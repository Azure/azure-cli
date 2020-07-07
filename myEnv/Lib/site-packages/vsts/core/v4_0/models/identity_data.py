# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class IdentityData(Model):
    """IdentityData.

    :param identity_ids:
    :type identity_ids: list of str
    """

    _attribute_map = {
        'identity_ids': {'key': 'identityIds', 'type': '[str]'}
    }

    def __init__(self, identity_ids=None):
        super(IdentityData, self).__init__()
        self.identity_ids = identity_ids
