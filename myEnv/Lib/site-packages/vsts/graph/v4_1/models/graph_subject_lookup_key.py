# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GraphSubjectLookupKey(Model):
    """GraphSubjectLookupKey.

    :param descriptor:
    :type descriptor: :class:`str <graph.v4_1.models.str>`
    """

    _attribute_map = {
        'descriptor': {'key': 'descriptor', 'type': 'str'}
    }

    def __init__(self, descriptor=None):
        super(GraphSubjectLookupKey, self).__init__()
        self.descriptor = descriptor
