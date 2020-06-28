# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GeoRegion(Model):
    """GeoRegion.

    :param region_code:
    :type region_code: str
    """

    _attribute_map = {
        'region_code': {'key': 'regionCode', 'type': 'str'}
    }

    def __init__(self, region_code=None):
        super(GeoRegion, self).__init__()
        self.region_code = region_code
