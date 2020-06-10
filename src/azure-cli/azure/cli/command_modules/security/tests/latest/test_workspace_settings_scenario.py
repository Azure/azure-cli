# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure_devtools.scenario_tests import AllowLargeResponse


class SecurityCenterWorkspaceSettingsTests(ScenarioTest):

    def test_security_workspace_settings(self):

        workspace_id = "/subscriptions/487bb485-b5b0-471e-9c0d-10717612f869/resourcegroups/myservice1/providers/microsoft.operationalinsights/workspaces/testservicews"

        self.cmd('az security workspace-setting create -n default --target-workspace ' + workspace_id)
        workspace_settings = self.cmd('az security workspace-setting list').get_output_in_json()

        assert len(workspace_settings) >= 0

        workspace_setting = self.cmd('az security workspace-setting show -n default').get_output_in_json()

        assert workspace_setting["workspaceId"].split('/')[-1] == workspace_id.split('/')[-1]

        self.cmd('az security workspace-setting delete -n default')

        workspace_settings = self.cmd('az security workspace-setting list').get_output_in_json()

        assert len(workspace_settings) == 0
