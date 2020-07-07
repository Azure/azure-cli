# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitRefUpdateResult(Model):
    """GitRefUpdateResult.

    :param custom_message: Custom message for the result object For instance, Reason for failing.
    :type custom_message: str
    :param is_locked: Whether the ref is locked or not
    :type is_locked: bool
    :param name: Ref name
    :type name: str
    :param new_object_id: New object ID
    :type new_object_id: str
    :param old_object_id: Old object ID
    :type old_object_id: str
    :param rejected_by: Name of the plugin that rejected the updated.
    :type rejected_by: str
    :param repository_id: Repository ID
    :type repository_id: str
    :param success: True if the ref update succeeded, false otherwise
    :type success: bool
    :param update_status: Status of the update from the TFS server.
    :type update_status: object
    """

    _attribute_map = {
        'custom_message': {'key': 'customMessage', 'type': 'str'},
        'is_locked': {'key': 'isLocked', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'new_object_id': {'key': 'newObjectId', 'type': 'str'},
        'old_object_id': {'key': 'oldObjectId', 'type': 'str'},
        'rejected_by': {'key': 'rejectedBy', 'type': 'str'},
        'repository_id': {'key': 'repositoryId', 'type': 'str'},
        'success': {'key': 'success', 'type': 'bool'},
        'update_status': {'key': 'updateStatus', 'type': 'object'}
    }

    def __init__(self, custom_message=None, is_locked=None, name=None, new_object_id=None, old_object_id=None, rejected_by=None, repository_id=None, success=None, update_status=None):
        super(GitRefUpdateResult, self).__init__()
        self.custom_message = custom_message
        self.is_locked = is_locked
        self.name = name
        self.new_object_id = new_object_id
        self.old_object_id = old_object_id
        self.rejected_by = rejected_by
        self.repository_id = repository_id
        self.success = success
        self.update_status = update_status
