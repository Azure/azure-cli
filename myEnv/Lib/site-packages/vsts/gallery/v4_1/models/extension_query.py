# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionQuery(Model):
    """ExtensionQuery.

    :param asset_types: When retrieving extensions with a query; frequently the caller only needs a small subset of the assets. The caller may specify a list of asset types that should be returned if the extension contains it. All other assets will not be returned.
    :type asset_types: list of str
    :param filters: Each filter is a unique query and will have matching set of extensions returned from the request. Each result will have the same index in the resulting array that the filter had in the incoming query.
    :type filters: list of :class:`QueryFilter <gallery.v4_1.models.QueryFilter>`
    :param flags: The Flags are used to deterine which set of information the caller would like returned for the matched extensions.
    :type flags: object
    """

    _attribute_map = {
        'asset_types': {'key': 'assetTypes', 'type': '[str]'},
        'filters': {'key': 'filters', 'type': '[QueryFilter]'},
        'flags': {'key': 'flags', 'type': 'object'}
    }

    def __init__(self, asset_types=None, filters=None, flags=None):
        super(ExtensionQuery, self).__init__()
        self.asset_types = asset_types
        self.filters = filters
        self.flags = flags
