# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure_devtools.scenario_tests import AllowLargeResponse
import re


class SecurityCenterTasksTests(ScenarioTest):

    @AllowLargeResponse()
    def test_security_tasks(self):

        tasks = self.cmd('az security task list').get_output_in_json()

        assert len(tasks) >= 0

        rg_task = next(task for task in tasks if "resourceGroups" in task["id"])

        match = re.search('resourceGroups/([^/]+)', rg_task["id"])

        task = self.cmd('az security task show -g ' + match.group(1) + ' -n ' + rg_task["name"]).get_output_in_json()

        assert task is not None

        subscription_task = next(task for task in tasks if "resourceGroups" not in task["id"])

        task = self.cmd('az security task show -n ' + subscription_task["name"]).get_output_in_json()

        assert task is not None
