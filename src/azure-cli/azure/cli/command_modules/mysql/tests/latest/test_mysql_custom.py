# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest.mock import MagicMock, patch

from ... import custom
from ..._params import load_arguments
from ..._util import normalize_mysql_tier


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


class MysqlAcceleratedLogsCustomTest(unittest.TestCase):

    def test_accelerated_logs_tier_behavior(self):
        self.assertEqual(
            'Enabled',
            custom._determine_acceleratedLogs('Enabled', 'GeneralPurpose'))
        self.assertEqual(
            'Disabled',
            custom._determine_acceleratedLogs(None, 'GeneralPurpose'))
        self.assertEqual(
            'Enabled',
            custom._determine_acceleratedLogs(None, 'MemoryOptimized'))
        self.assertEqual(
            'Disabled',
            custom._determine_acceleratedLogs('Enabled', 'Burstable'))


class MysqlTierNormalizationTest(unittest.TestCase):

    def test_business_critical_is_normalized_as_legacy_alias(self):
        self.assertEqual('MemoryOptimized', normalize_mysql_tier('BusinessCritical'))
        self.assertEqual('MemoryOptimized', normalize_mysql_tier('MemoryOptimized'))
        self.assertIsNone(normalize_mysql_tier(None))

    def test_all_tier_arguments_use_legacy_alias_normalizer(self):
        registrations = []
        loader = MagicMock()
        loader.argument_context.side_effect = \
            lambda command_name: _FakeArgumentContext(command_name, registrations)

        load_arguments(loader, None)

        tier_arg_types = {
            command_name: settings['arg_type']
            for command_name, argument_name, settings in registrations
            if argument_name == 'tier'
        }
        self.assertEqual({
            'mysql flexible-server create',
            'mysql flexible-server geo-restore',
            'mysql flexible-server import create',
            'mysql flexible-server replica create',
            'mysql flexible-server restore',
            'mysql flexible-server update'
        }, set(tier_arg_types))
        for command_name, arg_type in tier_arg_types.items():
            with self.subTest(command_name=command_name):
                self.assertIs(normalize_mysql_tier, arg_type.settings['type'])


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


class _FakeArgumentContext:

    def __init__(self, command_name, registrations):
        self.command_name = command_name
        self.registrations = registrations

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def argument(self, argument_name, *args, **settings):
        if args:
            settings['arg_type'] = args[0]
        self.registrations.append((self.command_name, argument_name, settings))


if __name__ == '__main__':
    unittest.main()
