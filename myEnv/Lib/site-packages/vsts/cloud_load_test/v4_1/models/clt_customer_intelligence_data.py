# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CltCustomerIntelligenceData(Model):
    """CltCustomerIntelligenceData.

    :param area:
    :type area: str
    :param feature:
    :type feature: str
    :param properties:
    :type properties: dict
    """

    _attribute_map = {
        'area': {'key': 'area', 'type': 'str'},
        'feature': {'key': 'feature', 'type': 'str'},
        'properties': {'key': 'properties', 'type': '{object}'}
    }

    def __init__(self, area=None, feature=None, properties=None):
        super(CltCustomerIntelligenceData, self).__init__()
        self.area = area
        self.feature = feature
        self.properties = properties
