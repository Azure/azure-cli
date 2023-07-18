# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from msrestazure.tools import parse_resource_id
import re


class SecurityCenterTasksTests(ScenarioTest):
    @AllowLargeResponse()
    def test_security_tasks(self):

        tasks = self.cmd('az security task list').get_output_in_json()

        self.assertGreaterEqual(len(tasks), 0)

        rg_task = next(task for task in tasks if parse_resource_id(task['id']).get('resource_group', None))

        self.kwargs.update({
            'task_id': parse_resource_id(rg_task['id'])['resource_group'],
            'task_name': rg_task["name"],
        })

        task = self.cmd('az security task show -g {task_id} -n {task_name}').get_output_in_json()

        self.assertIsNotNone(task)

        subscription_task = next(task for task in tasks if "resourceGroups" not in task["id"])

        task = self.cmd('az security task show -n ' + subscription_task["name"]).get_output_in_json()

        self.assertIsNotNone(task)
