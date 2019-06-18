# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import LiveScenarioTest
from azure_devtools.scenario_tests import AllowLargeResponse
import re


# TODO: revert when #9406 is addressed
class SecurityCenterAlertsTests(LiveScenarioTest):

    @AllowLargeResponse()
    def test_security_alerts(self):

        alerts = self.cmd('az security alert list').get_output_in_json()

        assert len(alerts) >= 0

        rg_alert = next(alert for alert in alerts if "resourceGroups" in alert["id"])

        match = re.search('resourceGroups/([^/]+)/.*/locations/([^/]+)', rg_alert["id"])

        alert = self.cmd('az security alert show -g ' + match.group(1) + ' -l ' + match.group(2) + ' -n ' + rg_alert["name"]).get_output_in_json()

        assert alert is not None

        self.cmd('az security alert update -g ' + match.group(1) + ' -l ' + match.group(2) + ' -n ' + rg_alert["name"] + ' --status activate')

        alert = self.cmd('az security alert show -g ' + match.group(1) + ' -l ' + match.group(2) + ' -n ' + rg_alert["name"]).get_output_in_json()

        assert alert["state"] == "Active"

        self.cmd('az security alert update -g ' + match.group(1) + ' -l ' + match.group(2) + ' -n ' + rg_alert["name"] + ' --status dismiss')

        alert = self.cmd('az security alert show -g ' + match.group(1) + ' -l ' + match.group(2) + ' -n ' + rg_alert["name"]).get_output_in_json()

        assert alert["state"] == "Dismissed"
