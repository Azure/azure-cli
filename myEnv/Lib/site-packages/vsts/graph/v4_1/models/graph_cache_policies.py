# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GraphCachePolicies(Model):
    """GraphCachePolicies.

    :param cache_size: Size of the cache
    :type cache_size: int
    """

    _attribute_map = {
        'cache_size': {'key': 'cacheSize', 'type': 'int'}
    }

    def __init__(self, cache_size=None):
        super(GraphCachePolicies, self).__init__()
        self.cache_size = cache_size
