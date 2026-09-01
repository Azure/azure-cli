# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest.mock import patch

from ... import custom


class MysqlFlexibleServerFirewallRuleCustomTest(unittest.TestCase):

    def test_firewall_rule_create_uses_properties_payload(self):
        client = _FakeFirewallRulesClient()

        with patch.object(custom, 'validate_public_access_server'):
            custom.firewall_rule_create_func(
                cmd=None,
                client=client,
                resource_group_name='rg',
                server_name='server',
                firewall_rule_name='allow-myip',
                start_ip_address='203.0.113.10',
                end_ip_address='203.0.113.10')

        self.assertEqual('rg', client.resource_group_name)
        self.assertEqual('server', client.server_name)
        self.assertEqual('allow-myip', client.firewall_rule_name)
        self.assertEqual({
            'properties': {
                'startIpAddress': '203.0.113.10',
                'endIpAddress': '203.0.113.10'
            }
        }, client.parameters.as_dict())


class MysqlFlexibleServerAdvancedThreatProtectionCustomTest(unittest.TestCase):

    def test_update_uses_properties_payload(self):
        client = _FakeAdvancedThreatProtectionClient()

        custom.flexible_server_advanced_threat_protection_update(
            cmd=None,
            client=client,
            resource_group_name='rg',
            server_name='server',
            state='Enabled')

        self.assertEqual('rg', client.resource_group_name)
        self.assertEqual('server', client.server_name)
        self.assertEqual('Default', client.advanced_threat_protection_name)
        self.assertEqual({
            'properties': {
                'state': 'Enabled'
            }
        }, client.parameters)


class _FakeFirewallRulesClient:

    def begin_create_or_update(self, resource_group_name, server_name, firewall_rule_name, parameters):
        self.resource_group_name = resource_group_name
        self.server_name = server_name
        self.firewall_rule_name = firewall_rule_name
        self.parameters = parameters
        return parameters


class _FakeAdvancedThreatProtectionClient:

    def begin_update(self, resource_group_name, server_name, advanced_threat_protection_name, parameters):
        self.resource_group_name = resource_group_name
        self.server_name = server_name
        self.advanced_threat_protection_name = advanced_threat_protection_name
        self.parameters = parameters
        return parameters


if __name__ == '__main__':
    unittest.main()
