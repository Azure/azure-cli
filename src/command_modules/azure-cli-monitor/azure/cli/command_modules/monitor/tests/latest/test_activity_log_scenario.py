# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from time import sleep
from azure.cli.testsdk import LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


# This is a live test because the start and end time can't be determined dynamically
class TestActivityLogScenarios(LiveScenarioTest):
    @ResourceGroupPreparer(location='southcentralus')
    @StorageAccountPreparer()
    def test_activity_log_list_scenario(self, resource_group):

        for count in range(3):
            logs = self.cmd('monitor activity-log list --resource-group {}'.format(resource_group)).get_output_in_json()
            if len(logs) > 0:
                break

            sleep(2 ** count)  # Wait 1, 2, and 4 seconds incrementally to let the activity log catch up.
        else:
            self.assertTrue(False, 'After three try the command fails to retrieve any activity log.')
