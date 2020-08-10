# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitConflictUpdateResult(Model):
    """GitConflictUpdateResult.

    :param conflict_id: Conflict ID that was provided by input
    :type conflict_id: int
    :param custom_message: Reason for failing
    :type custom_message: str
    :param updated_conflict: New state of the conflict after updating
    :type updated_conflict: :class:`GitConflict <git.v4_1.models.GitConflict>`
    :param update_status: Status of the update on the server
    :type update_status: object
    """

    _attribute_map = {
        'conflict_id': {'key': 'conflictId', 'type': 'int'},
        'custom_message': {'key': 'customMessage', 'type': 'str'},
        'updated_conflict': {'key': 'updatedConflict', 'type': 'GitConflict'},
        'update_status': {'key': 'updateStatus', 'type': 'object'}
    }

    def __init__(self, conflict_id=None, custom_message=None, updated_conflict=None, update_status=None):
        super(GitConflictUpdateResult, self).__init__()
        self.conflict_id = conflict_id
        self.custom_message = custom_message
        self.updated_conflict = updated_conflict
        self.update_status = update_status
