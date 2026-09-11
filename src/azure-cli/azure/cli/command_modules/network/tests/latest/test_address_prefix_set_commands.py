# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest


class TestAddressPrefixSetAAZCommands(unittest.TestCase):
    def test_parent_and_child_commands_are_registered(self):
        from azure.cli.core.mock import DummyCli
        from azure.cli.command_modules.network import NetworkCommandsLoader

        parent_loader = NetworkCommandsLoader(cli_ctx=DummyCli())
        parent_commands = parent_loader.load_command_table(['network', 'asg', 'create'])
        self.assertIn('network asg create', parent_commands)

        child_loader = NetworkCommandsLoader(cli_ctx=DummyCli())
        child_commands = child_loader.load_command_table(
            ['network', 'asg', 'address-prefix-set', 'create']
        )
        self.assertIn('network asg address-prefix-set create', child_commands)

    def test_address_prefix_set_command_schemas(self):
        from azure.cli.command_modules.network.aaz.latest.network.asg.address_prefix_set._create import Create
        from azure.cli.command_modules.network.aaz.latest.network.asg.address_prefix_set._update import Update

        create_schema = Create._build_arguments_schema()
        self.assertTrue(create_schema.resource_group._required)
        self.assertTrue(create_schema.application_security_group_name._required)
        self.assertTrue(create_schema.name._required)
        self.assertTrue(create_schema.address_prefixes._required)
        self.assertEqual(create_schema.address_prefixes._options, ['--address-prefixes'])
        self.assertEqual(Create._aaz_info['version'], '2025-09-01')

        update_schema = Update._build_arguments_schema()
        self.assertFalse(update_schema.address_prefixes._required)
        self.assertTrue(update_schema.address_prefixes._nullable)
        self.assertTrue(Update.AZ_SUPPORT_GENERIC_UPDATE)


if __name__ == '__main__':
    unittest.main()
