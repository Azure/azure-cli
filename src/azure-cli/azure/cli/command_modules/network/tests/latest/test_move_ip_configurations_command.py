# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest


class TestMoveIpConfigurationsAAZCommand(unittest.TestCase):
    def test_move_ip_configurations_command_is_registered(self):
        from azure.cli.core.mock import DummyCli
        from azure.cli.command_modules.network import NetworkCommandsLoader

        loader = NetworkCommandsLoader(cli_ctx=DummyCli())
        command_table = loader.load_command_table(
            ['network', 'vnet', 'move-ip-configurations']
        )
        self.assertIn('network vnet move-ip-configurations', command_table)

    def test_move_ip_configurations_command_schema(self):
        from azure.cli.command_modules.network.aaz.latest.network.vnet._move_ip_configurations import (
            MoveIpConfigurations,
        )

        schema = MoveIpConfigurations._build_arguments_schema()
        self.assertTrue(schema.move_ip_configuration_items._required)
        self.assertIn('--move-items', schema.move_ip_configuration_items._options)
        item = schema.move_ip_configuration_items.Element
        self.assertTrue(item.source_ip_configuration._required)
        self.assertTrue(item.source_ip_configuration.id._required)
        self.assertTrue(item.target_ip_configuration._required)
        self.assertTrue(item.target_ip_configuration.id._required)
        self.assertEqual(MoveIpConfigurations._aaz_info['version'], '2025-09-01')
        operation = MoveIpConfigurations.VirtualNetworksMoveIpConfigurations
        self.assertEqual(operation.method.fget(None), 'POST')


if __name__ == '__main__':
    unittest.main()
