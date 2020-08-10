# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionDataCollectionQuery(Model):
    """ExtensionDataCollectionQuery.

    :param collections: A list of collections to query
    :type collections: list of :class:`ExtensionDataCollection <extension-management.v4_0.models.ExtensionDataCollection>`
    """

    _attribute_map = {
        'collections': {'key': 'collections', 'type': '[ExtensionDataCollection]'}
    }

    def __init__(self, collections=None):
        super(ExtensionDataCollectionQuery, self).__init__()
        self.collections = collections
