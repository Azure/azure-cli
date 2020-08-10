# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentPoolMaintenanceOptions(Model):
    """TaskAgentPoolMaintenanceOptions.

    :param working_directory_expiration_in_days: time to consider a System.DefaultWorkingDirectory is stale
    :type working_directory_expiration_in_days: int
    """

    _attribute_map = {
        'working_directory_expiration_in_days': {'key': 'workingDirectoryExpirationInDays', 'type': 'int'}
    }

    def __init__(self, working_directory_expiration_in_days=None):
        super(TaskAgentPoolMaintenanceOptions, self).__init__()
        self.working_directory_expiration_in_days = working_directory_expiration_in_days
