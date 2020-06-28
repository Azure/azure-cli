# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class LicensingOverride(Model):
    """LicensingOverride.

    :param behavior: How the inclusion of this contribution should change based on licensing
    :type behavior: object
    :param id: Fully qualified contribution id which we want to define licensing behavior for
    :type id: str
    """

    _attribute_map = {
        'behavior': {'key': 'behavior', 'type': 'object'},
        'id': {'key': 'id', 'type': 'str'}
    }

    def __init__(self, behavior=None, id=None):
        super(LicensingOverride, self).__init__()
        self.behavior = behavior
        self.id = id
