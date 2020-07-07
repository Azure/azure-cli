# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class License(Model):
    """License.

    :param source: Gets the source of the license
    :type source: object
    """

    _attribute_map = {
        'source': {'key': 'source', 'type': 'object'}
    }

    def __init__(self, source=None):
        super(License, self).__init__()
        self.source = source
