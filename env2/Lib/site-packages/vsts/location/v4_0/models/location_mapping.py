# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class LocationMapping(Model):
    """LocationMapping.

    :param access_mapping_moniker:
    :type access_mapping_moniker: str
    :param location:
    :type location: str
    """

    _attribute_map = {
        'access_mapping_moniker': {'key': 'accessMappingMoniker', 'type': 'str'},
        'location': {'key': 'location', 'type': 'str'}
    }

    def __init__(self, access_mapping_moniker=None, location=None):
        super(LocationMapping, self).__init__()
        self.access_mapping_moniker = access_mapping_moniker
        self.location = location
