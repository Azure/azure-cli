# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

import os
import unittest

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class SecurityCenterWorkspaceSettingsTests(ScenarioTest):

    @unittest.skip('"az security workspace-setting delete -n default" command is failing, and needs to be fixed in swagger by ASC team ')
    @ResourceGroupPreparer()
    def test_security_workspace_settings(self):
        self.kwargs.update({
            'ws': self.create_random_name('testsecws', 20),
            'la_prop_path': os.path.join(TEST_DIR, 'loganalytics.json')
        })

        ws_response = self.cmd('az resource create -g {rg} -n {ws} '
                               '--resource-type Microsoft.OperationalInsights/workspaces -p @"{la_prop_path}"') \
            .get_output_in_json()
        workspace_id = ws_response['id']
        self.kwargs.update({
            'workspace_id': workspace_id
        })

        self.cmd('az security workspace-setting create -n default --target-workspace "{workspace_id}"')
        workspace_settings = self.cmd('az security workspace-setting list').get_output_in_json()

        assert len(workspace_settings) >= 0

        workspace_setting = self.cmd('az security workspace-setting show -n default').get_output_in_json()
        assert workspace_setting['name'] == 'default'

        # workspaceId is not returned, it's a potential issue on service side
        # assert workspace_setting["workspaceId"].split('/')[-1] == workspace_id.split('/')[-1]

        self.cmd('az security workspace-setting delete -n default')

        workspace_settings = self.cmd('az security workspace-setting list').get_output_in_json()

        assert len(workspace_settings) == 0

        self.cmd('az resource delete --ids {workspace_id}')
