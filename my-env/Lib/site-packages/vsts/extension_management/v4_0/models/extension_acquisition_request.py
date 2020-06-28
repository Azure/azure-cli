# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionAcquisitionRequest(Model):
    """ExtensionAcquisitionRequest.

    :param assignment_type: How the item is being assigned
    :type assignment_type: object
    :param billing_id: The id of the subscription used for purchase
    :type billing_id: str
    :param item_id: The marketplace id (publisherName.extensionName) for the item
    :type item_id: str
    :param operation_type: The type of operation, such as install, request, purchase
    :type operation_type: object
    :param properties: Additional properties which can be added to the request.
    :type properties: :class:`object <extension-management.v4_0.models.object>`
    :param quantity: How many licenses should be purchased
    :type quantity: int
    """

    _attribute_map = {
        'assignment_type': {'key': 'assignmentType', 'type': 'object'},
        'billing_id': {'key': 'billingId', 'type': 'str'},
        'item_id': {'key': 'itemId', 'type': 'str'},
        'operation_type': {'key': 'operationType', 'type': 'object'},
        'properties': {'key': 'properties', 'type': 'object'},
        'quantity': {'key': 'quantity', 'type': 'int'}
    }

    def __init__(self, assignment_type=None, billing_id=None, item_id=None, operation_type=None, properties=None, quantity=None):
        super(ExtensionAcquisitionRequest, self).__init__()
        self.assignment_type = assignment_type
        self.billing_id = billing_id
        self.item_id = item_id
        self.operation_type = operation_type
        self.properties = properties
        self.quantity = quantity
