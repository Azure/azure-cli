# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentPoolMaintenanceRetentionPolicy(Model):
    """TaskAgentPoolMaintenanceRetentionPolicy.

    :param number_of_history_records_to_keep: Number of records to keep for maintenance job executed with this definition.
    :type number_of_history_records_to_keep: int
    """

    _attribute_map = {
        'number_of_history_records_to_keep': {'key': 'numberOfHistoryRecordsToKeep', 'type': 'int'}
    }

    def __init__(self, number_of_history_records_to_keep=None):
        super(TaskAgentPoolMaintenanceRetentionPolicy, self).__init__()
        self.number_of_history_records_to_keep = number_of_history_records_to_keep
