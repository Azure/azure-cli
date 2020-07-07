# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AcquisitionOptions(Model):
    """AcquisitionOptions.

    :param default_operation: Default Operation for the ItemId in this target
    :type default_operation: :class:`AcquisitionOperation <extension-management.v4_1.models.AcquisitionOperation>`
    :param item_id: The item id that this options refer to
    :type item_id: str
    :param operations: Operations allowed for the ItemId in this target
    :type operations: list of :class:`AcquisitionOperation <extension-management.v4_1.models.AcquisitionOperation>`
    :param properties: Additional properties which can be added to the request.
    :type properties: :class:`object <extension-management.v4_1.models.object>`
    :param target: The target that this options refer to
    :type target: str
    """

    _attribute_map = {
        'default_operation': {'key': 'defaultOperation', 'type': 'AcquisitionOperation'},
        'item_id': {'key': 'itemId', 'type': 'str'},
        'operations': {'key': 'operations', 'type': '[AcquisitionOperation]'},
        'properties': {'key': 'properties', 'type': 'object'},
        'target': {'key': 'target', 'type': 'str'}
    }

    def __init__(self, default_operation=None, item_id=None, operations=None, properties=None, target=None):
        super(AcquisitionOptions, self).__init__()
        self.default_operation = default_operation
        self.item_id = item_id
        self.operations = operations
        self.properties = properties
        self.target = target
