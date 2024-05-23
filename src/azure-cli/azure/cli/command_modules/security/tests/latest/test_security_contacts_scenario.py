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

        contact = self.cmd('az security contact create -n default --emails john@contoso.com --phone 214-275-4038 --notifications-by-role state=On roles=[Owner,ServiceAdmin] --alert-notifications state=On minimalSeverity=Low').get_output_in_json()
        
        assert contact["name"] == "default"
        assert contact["emails"] == "john@contoso.com"
        
        security_contacts = self.cmd('az security contact list').get_output_in_json()
        assert len(security_contacts) > 0

        contact = self.cmd('az security contact show -n default').get_output_in_json()

        assert contact["emails"] == "john@contoso.com"

        contact = self.cmd('az security contact create -n default --emails john@contoso.com;lisa@contoso.com --phone 214-275-4038 --notifications-by-role state=On roles=[Owner,ServiceAdmin] --alert-notifications state=On minimalSeverity=Low').get_output_in_json()

        contact = self.cmd('az security contact show -n default').get_output_in_json()

        assert contact["emails"] == "john@contoso.com;lisa@contoso.com"

        self.cmd('az security contact delete -n default --yes')

        security_contacts = self.cmd('az security contact list').get_output_in_json()
        assert len(security_contacts) == previous_contacts_count
