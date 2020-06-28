# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProfileRegion(Model):
    """ProfileRegion.

    :param code: The two-letter code defined in ISO 3166 for the country/region.
    :type code: str
    :param name: Localized country/region name
    :type name: str
    """

    _attribute_map = {
        'code': {'key': 'code', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, code=None, name=None):
        super(ProfileRegion, self).__init__()
        self.code = code
        self.name = name
