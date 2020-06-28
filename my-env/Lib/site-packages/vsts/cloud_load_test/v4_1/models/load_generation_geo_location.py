# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class LoadGenerationGeoLocation(Model):
    """LoadGenerationGeoLocation.

    :param location:
    :type location: str
    :param percentage:
    :type percentage: int
    """

    _attribute_map = {
        'location': {'key': 'location', 'type': 'str'},
        'percentage': {'key': 'percentage', 'type': 'int'}
    }

    def __init__(self, location=None, percentage=None):
        super(LoadGenerationGeoLocation, self).__init__()
        self.location = location
        self.percentage = percentage
