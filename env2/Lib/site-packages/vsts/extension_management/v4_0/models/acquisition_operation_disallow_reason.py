# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AcquisitionOperationDisallowReason(Model):
    """AcquisitionOperationDisallowReason.

    :param message: User-friendly message clarifying the reason for disallowance
    :type message: str
    :param type: Type of reason for disallowance - AlreadyInstalled, UnresolvedDemand, etc.
    :type type: str
    """

    _attribute_map = {
        'message': {'key': 'message', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, message=None, type=None):
        super(AcquisitionOperationDisallowReason, self).__init__()
        self.message = message
        self.type = type
