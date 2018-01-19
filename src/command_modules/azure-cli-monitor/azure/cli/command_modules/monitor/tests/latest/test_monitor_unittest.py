# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

try:
    import unittest.mock as mock
except ImportError:
    import mock

from knack.util import CLIError

from azure.cli.command_modules.monitor.operations.autoscale_settings import scaffold_autoscale_settings_parameters


class FilterBuilderTests(unittest.TestCase):
    def test_scaffold_autoscale_settings_parameters(self):
        template = scaffold_autoscale_settings_parameters(None)
        self.assertTrue(template)
        self.assertTrue(isinstance(template, dict))


def _mock_get_subscription_id(_):
    return '00000000-0000-0000-0000-000000000000'


class MonitorNameOrIdTest(unittest.TestCase):
    def _build_namespace(self, name_or_id=None, resource_group=None, provider_namespace=None, parent=None,
                         resource_type=None):
        from argparse import Namespace
        ns = Namespace()
        ns.name_or_id = name_or_id
        ns.resource_group_name = resource_group
        ns.namespace = provider_namespace
        ns.parent = parent
        ns.resource_type = resource_type
        return ns

    @mock.patch('azure.cli.core.commands.client_factory.get_subscription_id', _mock_get_subscription_id)
    def test_monitor_resource_id(self):
        from azure.cli.command_modules.monitor.validators import get_target_resource_validator
        from azure.cli.testsdk import TestCli

        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()
        validator = get_target_resource_validator('name_or_id', True)

        id = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.Compute/' \
             'virtualMachines/vm1'

        # must supply name or ID
        ns = self._build_namespace()
        with self.assertRaises(CLIError):
            validator(cmd, ns)

        # must only supply ID or name parameters
        ns = self._build_namespace(id, 'my-rg', 'blahblah', 'stuff')
        with self.assertRaises(CLIError):
            validator(cmd, ns)

        # error on invalid ID
        ns = self._build_namespace('bad-id')
        with self.assertRaises(CLIError):
            validator(cmd, ns)

        # allow Provider/Type syntax (same as resource commands)
        ns = self._build_namespace('vm1', 'my-rg', None, None, 'Microsoft.Compute/virtualMachines')
        validator(cmd, ns)
        self.assertEqual(ns.name_or_id, id)

        # allow Provider and Type separate
        ns = self._build_namespace('vm1', 'my-rg', 'Microsoft.Compute', None, 'virtualMachines')
        validator(cmd, ns)
        self.assertEqual(ns.name_or_id, id)

        # verify works with parent
        id = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.Compute/' \
             'fakeType/type1/anotherFakeType/type2/virtualMachines/vm1'
        ns = self._build_namespace('vm1', 'my-rg', 'Microsoft.Compute', 'fakeType/type1/anotherFakeType/type2',
                                   'virtualMachines')
        validator(cmd, ns)
        self.assertEqual(ns.name_or_id, id)

        # verify extra parameters are removed
        self.assertFalse(hasattr(ns, 'resource_name'))
        self.assertFalse(hasattr(ns, 'namespace'))
        self.assertFalse(hasattr(ns, 'parent'))
        self.assertFalse(hasattr(ns, 'resource_type'))
