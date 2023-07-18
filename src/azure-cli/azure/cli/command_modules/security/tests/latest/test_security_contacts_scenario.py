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

        self.cmd('az security contact create -n default1 --email john@contoso.com --alert-notifications off --alerts-admins off')

        security_contacts = self.cmd('az security contact list').get_output_in_json()
        assert len(security_contacts) >= 0

        contact = self.cmd('az security contact show -n default1').get_output_in_json()

        assert contact["email"] == "john@contoso.com"

        self.cmd('az security contact create -n default1 --email lisa@contoso.com --alert-notifications off --alerts-admins off')

        contact = self.cmd('az security contact show -n default1').get_output_in_json()

        assert contact["email"] == "lisa@contoso.com"

        self.cmd('az security contact delete -n default1')

        security_contacts = self.cmd('az security contact list').get_output_in_json()
        assert len(security_contacts) == previous_contacts_count
