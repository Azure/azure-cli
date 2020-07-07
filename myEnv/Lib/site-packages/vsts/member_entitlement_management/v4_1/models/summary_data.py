# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SummaryData(Model):
    """SummaryData.

    :param assigned: Count of Licenses already assigned.
    :type assigned: int
    :param available: Available Count.
    :type available: int
    :param included_quantity: Quantity
    :type included_quantity: int
    :param total: Total Count.
    :type total: int
    """

    _attribute_map = {
        'assigned': {'key': 'assigned', 'type': 'int'},
        'available': {'key': 'available', 'type': 'int'},
        'included_quantity': {'key': 'includedQuantity', 'type': 'int'},
        'total': {'key': 'total', 'type': 'int'}
    }

    def __init__(self, assigned=None, available=None, included_quantity=None, total=None):
        super(SummaryData, self).__init__()
        self.assigned = assigned
        self.available = available
        self.included_quantity = included_quantity
        self.total = total
