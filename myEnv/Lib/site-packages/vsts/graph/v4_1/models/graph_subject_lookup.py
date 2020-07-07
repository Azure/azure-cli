# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GraphSubjectLookup(Model):
    """GraphSubjectLookup.

    :param lookup_keys:
    :type lookup_keys: list of :class:`GraphSubjectLookupKey <graph.v4_1.models.GraphSubjectLookupKey>`
    """

    _attribute_map = {
        'lookup_keys': {'key': 'lookupKeys', 'type': '[GraphSubjectLookupKey]'}
    }

    def __init__(self, lookup_keys=None):
        super(GraphSubjectLookup, self).__init__()
        self.lookup_keys = lookup_keys
