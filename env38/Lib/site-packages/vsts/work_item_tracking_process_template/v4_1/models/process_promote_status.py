# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProcessPromoteStatus(Model):
    """ProcessPromoteStatus.

    :param complete: Number of projects for which promote is complete.
    :type complete: int
    :param id: ID of the promote operation.
    :type id: str
    :param message: The error message assoicated with the promote operation. The string will be empty if there are no errors.
    :type message: str
    :param pending: Number of projects for which promote is pending.
    :type pending: int
    :param remaining_retries: The remaining retries.
    :type remaining_retries: int
    :param successful: True if promote finished all the projects successfully. False if still inprogress or any project promote failed.
    :type successful: bool
    """

    _attribute_map = {
        'complete': {'key': 'complete', 'type': 'int'},
        'id': {'key': 'id', 'type': 'str'},
        'message': {'key': 'message', 'type': 'str'},
        'pending': {'key': 'pending', 'type': 'int'},
        'remaining_retries': {'key': 'remainingRetries', 'type': 'int'},
        'successful': {'key': 'successful', 'type': 'bool'}
    }

    def __init__(self, complete=None, id=None, message=None, pending=None, remaining_retries=None, successful=None):
        super(ProcessPromoteStatus, self).__init__()
        self.complete = complete
        self.id = id
        self.message = message
        self.pending = pending
        self.remaining_retries = remaining_retries
        self.successful = successful
