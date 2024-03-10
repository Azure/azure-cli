# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class SecurityCenterSecurityContactsTests(ScenarioTest):

    def test_security_contacts(self):

        security_contacts = self.cmd('az security contact list').get_output_in_json()
        previous_contacts_count = len(security_contacts)
        assert previous_contacts_count >= 0

        self.kwargs.update({
            'notificationsByRole': dict(state = "On", roles = ["Owner"]),
            'alertNotifications': dict(state = "On", minimalSeverity = "Low")
        })

        self.kwargs['notifications-by-role'] = dict(state = "On", roles = ["Owner"])

        # self.cmd('az security contact create -n \'default\' --emails \'john@contoso.com\' --phone \'214-275-4038\' --notifications-by-role \"{"state":"On","roles":["Owner"]}\" --alert-notifications \"{"state":"On","minimalSeverity":"Low"}\"')
        self.cmd('az security contact create -n default --emails john@contoso.com --phone 214-275-4038 --notifications-by-role {notificationsByRole} --alert-notifications {alertNotifications}')

        security_contacts = self.cmd('az security contact list').get_output_in_json()
        assert len(security_contacts) > 0

        # contact = self.cmd('az security contact show -n default').get_output_in_json()

        # assert contact["emails"] == "john@contoso.com"

        # self.cmd('az security contact create -n \'default\' --emails \'john@contoso.com\' --phone \'214-275-4038\' --notifications-by-role \"{"state":"On","roles":["Owner"]}\" --alert-notifications \"{"state":"On","minimalSeverity":"Low"}\"')

        # contact = self.cmd('az security contact show -n default').get_output_in_json()

        # assert contact["emails"] == "lisa@contoso.com"

        # self.cmd('az security contact delete -n default')

        # security_contacts = self.cmd('az security contact list').get_output_in_json()
        # assert len(security_contacts) == previous_contacts_count
