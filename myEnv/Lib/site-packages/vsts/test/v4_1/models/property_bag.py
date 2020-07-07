# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PropertyBag(Model):
    """PropertyBag.

    :param bag: Generic store for test session data
    :type bag: dict
    """

    _attribute_map = {
        'bag': {'key': 'bag', 'type': '{str}'}
    }

    def __init__(self, bag=None):
        super(PropertyBag, self).__init__()
        self.bag = bag
