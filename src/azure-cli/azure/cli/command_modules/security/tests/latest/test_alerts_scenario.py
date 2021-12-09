# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
import re


# TODO: revert when #9406 is addressed
class SecurityCenterAlertsTests(ScenarioTest):

    @record_only()  # this test relies on existing security alerts in resource groups
    def test_security_alerts(self):

        alerts = self.cmd('az security alert list').get_output_in_json()

        assert len(alerts) >= 0

        rg_alert = next(alert for alert in alerts if "resourceGroups" in alert["id"])

        match = re.search('resourceGroups/([^/]+)/.*/locations/([^/]+)', rg_alert["id"])

        alertName = rg_alert["name"]

        rg = match.group(1)

        location = match.group(2)

        alert = self.cmd('az security alert show -g {} -l {} -n {}'.format(rg, location, alertName)).get_output_in_json()

        assert alert is not None

        # check rg level

        self.cmd('az security alert update -g {} -l {} -n {} --status Activate'.format(rg, location, alertName))

        alert = self.cmd('az security alert show -g {} -l {} -n {}'.format(rg, location, alertName)).get_output_in_json()

        assert alert["status"] == "Active"

        self.cmd('az security alert update -g {} -l {} -n {} --status Dismiss'.format(rg, location, alertName))

        alert = self.cmd('az security alert show -g {} -l {} -n {}'.format(rg, location, alertName)).get_output_in_json()

        assert alert["status"] == "Dismissed"

        self.cmd('az security alert update -g {} -l {} -n {} --status Resolve'.format(rg, location, alertName))

        alert = self.cmd('az security alert show -g {} -l {} -n {}'.format(rg, location, alertName)).get_output_in_json()

        assert alert["status"] == "Resolved"

        # check subscription level

        self.cmd('az security alert update -l {} -n {} --status Activate'.format(location, alertName))

        alert = self.cmd('az security alert show -l {} -n {}'.format(location, alertName)).get_output_in_json()

        assert alert["status"] == "Active"

        self.cmd('az security alert update -l {} -n {} --status Dismiss'.format(location, alertName))

        alert = self.cmd('az security alert show -l {} -n {}'.format(location, alertName)).get_output_in_json()

        assert alert["status"] == "Dismissed"

        self.cmd('az security alert update -l {} -n {} --status Resolve'.format(location, alertName))

        alert = self.cmd('az security alert show -l {} -n {}'.format(location, alertName)).get_output_in_json()

        assert alert["status"] == "Resolved"

        # reset alert to active

        self.cmd('az security alert update -l {} -n {} --status Activate'.format(location, alertName))

        alert = self.cmd('az security alert show -l {} -n {}'.format(location, alertName)).get_output_in_json()

        assert alert["status"] == "Active"
