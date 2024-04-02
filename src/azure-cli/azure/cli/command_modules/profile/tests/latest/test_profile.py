# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests.const import MOCKED_SUBSCRIPTION_ID, MOCKED_TENANT_ID
from azure.cli.testsdk.patches import MOCKED_USER_NAME


class ProfileTest(ScenarioTest):

    def test_account_show(self):
        # Force this test to generate a recording file so that this test can run in playback mode.
        self.cmd('az rest -u /subscriptions/{{subscriptionId}}/locations?api-version=2019-11-01')

        result = self.cmd('account show').get_output_in_json()

        if self.in_recording:
            # During recording, the current real user is returned.
            assert 'id' in result
        else:
            # During playback, a mocked user is returned, so we have more to check.
            assert result['id'] == MOCKED_SUBSCRIPTION_ID
            assert result['tenantId'] == MOCKED_TENANT_ID
            assert result['user']['name'] == MOCKED_USER_NAME


if __name__ == '__main__':
    unittest.main()
