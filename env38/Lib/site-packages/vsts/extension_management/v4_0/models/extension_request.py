# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionRequest(Model):
    """ExtensionRequest.

    :param reject_message: Required message supplied if the request is rejected
    :type reject_message: str
    :param request_date: Date at which the request was made
    :type request_date: datetime
    :param requested_by: Represents the user who made the request
    :type requested_by: :class:`IdentityRef <extension-management.v4_0.models.IdentityRef>`
    :param request_message: Optional message supplied by the requester justifying the request
    :type request_message: str
    :param request_state: Represents the state of the request
    :type request_state: object
    :param resolve_date: Date at which the request was resolved
    :type resolve_date: datetime
    :param resolved_by: Represents the user who resolved the request
    :type resolved_by: :class:`IdentityRef <extension-management.v4_0.models.IdentityRef>`
    """

    _attribute_map = {
        'reject_message': {'key': 'rejectMessage', 'type': 'str'},
        'request_date': {'key': 'requestDate', 'type': 'iso-8601'},
        'requested_by': {'key': 'requestedBy', 'type': 'IdentityRef'},
        'request_message': {'key': 'requestMessage', 'type': 'str'},
        'request_state': {'key': 'requestState', 'type': 'object'},
        'resolve_date': {'key': 'resolveDate', 'type': 'iso-8601'},
        'resolved_by': {'key': 'resolvedBy', 'type': 'IdentityRef'}
    }

    def __init__(self, reject_message=None, request_date=None, requested_by=None, request_message=None, request_state=None, resolve_date=None, resolved_by=None):
        super(ExtensionRequest, self).__init__()
        self.reject_message = reject_message
        self.request_date = request_date
        self.requested_by = requested_by
        self.request_message = request_message
        self.request_state = request_state
        self.resolve_date = resolve_date
        self.resolved_by = resolved_by
