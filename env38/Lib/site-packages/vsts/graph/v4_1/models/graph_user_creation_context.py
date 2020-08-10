# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GraphUserCreationContext(Model):
    """GraphUserCreationContext.

    :param storage_key: Optional: If provided, we will use this identifier for the storage key of the created user
    :type storage_key: str
    """

    _attribute_map = {
        'storage_key': {'key': 'storageKey', 'type': 'str'}
    }

    def __init__(self, storage_key=None):
        super(GraphUserCreationContext, self).__init__()
        self.storage_key = storage_key
