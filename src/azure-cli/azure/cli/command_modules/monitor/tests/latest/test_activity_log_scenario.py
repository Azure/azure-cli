# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from time import sleep
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from azure_devtools.scenario_tests import AllowLargeResponse

from knack.util import CLIError


# This is a live test because the start and end time can't be determined dynamically
class TestActivityLogScenarios(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location='southcentralus')
    @StorageAccountPreparer()
    def test_activity_log_list_scenario(self, resource_group):
        with self.assertRaisesRegexp(CLIError, 'start time cannot be more than 90 days in the past'):
            self.cmd('monitor activity-log list --start-time 2018-01-01T00:00:00Z --end-time 2999-01-01T00:00:00Z')
