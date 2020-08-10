# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemDeleteUpdate(Model):
    """WorkItemDeleteUpdate.

    :param is_deleted: Sets a value indicating whether this work item is deleted.
    :type is_deleted: bool
    """

    _attribute_map = {
        'is_deleted': {'key': 'isDeleted', 'type': 'bool'}
    }

    def __init__(self, is_deleted=None):
        super(WorkItemDeleteUpdate, self).__init__()
        self.is_deleted = is_deleted
