# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TfvcBranchMapping(Model):
    """TfvcBranchMapping.

    :param depth:
    :type depth: str
    :param server_item:
    :type server_item: str
    :param type:
    :type type: str
    """

    _attribute_map = {
        'depth': {'key': 'depth', 'type': 'str'},
        'server_item': {'key': 'serverItem', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, depth=None, server_item=None, type=None):
        super(TfvcBranchMapping, self).__init__()
        self.depth = depth
        self.server_item = server_item
        self.type = type
