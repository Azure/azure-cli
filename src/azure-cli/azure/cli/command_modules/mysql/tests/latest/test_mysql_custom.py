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


class MysqlFlexibleServerListSkusCustomTest(unittest.TestCase):

    def test_list_skus_preserves_memory_optimized_tier(self):
        capabilities = [_FakeCapability('MemoryOptimized')]
        client = _FakeLocationCapabilitiesClient(capabilities)

        result = custom.flexible_list_skus(cmd=None, client=client, location='eastus')

        self.assertIs(capabilities, result)
        self.assertEqual('eastus', client.location)
        self.assertEqual(
            'MemoryOptimized',
            result[0].supported_flexible_server_editions[0].name)


class _FakeFirewallRulesClient:

    def begin_create_or_update(self, resource_group_name, server_name, firewall_rule_name, parameters):
        self.resource_group_name = resource_group_name
        self.server_name = server_name
        self.firewall_rule_name = firewall_rule_name
        self.parameters = parameters
        return parameters


class _FakeCapability:

    def __init__(self, tier_name):
        self.supported_flexible_server_editions = [_FakeEdition(tier_name)]


class _FakeEdition:

    def __init__(self, name):
        self.name = name


class _FakeLocationCapabilitiesClient:

    def __init__(self, result):
        self.result = result
        self.location = None

    def list(self, location):
        self.location = location
        return self.result


if __name__ == '__main__':
    unittest.main()
