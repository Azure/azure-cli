# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import inspect
import unittest
from unittest import mock

from azure.cli.core.azclierror import ValidationError
from azure.cli.core.mock import DummyCli
from azure.cli.command_modules.postgresql import PostgreSQLCommandsLoader
from azure.cli.command_modules.postgresql.commands.custom_commands import flexible_server_restore
from azure.cli.command_modules.postgresql.utils.validators import pg_restore_tier_validator

RESTORE_COMMAND = 'postgres flexible-server restore'

# Shape mirrors the 'sku_info' entry returned by get_postgres_location_capability_info.
SKU_INFO = {
    'Burstable': {'skus': {'Standard_B1ms', 'Standard_B2s'}},
    'GeneralPurpose': {'skus': {'Standard_D2s_v3', 'Standard_D4s_v3'}},
    'MemoryOptimized': {'skus': {'Standard_E2ds_v4', 'Standard_E4ds_v4'}},
}


def _load_command_and_arguments(command):
    cli = DummyCli(commands_loader_cls=PostgreSQLCommandsLoader)
    loader = PostgreSQLCommandsLoader(cli)
    cli.invocation = mock.MagicMock()
    cli.invocation.commands_loader = loader
    loader.command_name = command
    loader.load_command_table(None)
    loader.load_arguments(command)
    loader._update_command_definitions()
    return loader


class RestoreSkuArgumentsTest(unittest.TestCase):
    """`az postgres flexible-server restore` must expose --sku-name and --tier."""

    def test_sku_name_and_tier_are_registered(self):
        loader = _load_command_and_arguments(RESTORE_COMMAND)
        arguments = loader.argument_registry.arguments.get(RESTORE_COMMAND, {})

        for dest, option in (('sku_name', '--sku-name'), ('tier', '--tier')):
            arg = arguments.get(dest)
            self.assertIsNotNone(arg, "'{}' not found in argument registry".format(dest))
            self.assertIn(option, arg.settings.get('options_list'))

    def test_registered_arguments_are_accepted_by_the_custom_command(self):
        """An argument registered for a dest the custom command does not accept is silently dropped."""
        loader = _load_command_and_arguments(RESTORE_COMMAND)
        accepted = set(inspect.signature(flexible_server_restore).parameters)
        registered = set(loader.argument_registry.arguments.get(RESTORE_COMMAND, {}))

        self.assertEqual(registered - accepted, set())


class RestoreTierValidatorTest(unittest.TestCase):

    def test_upgrading_tier_is_allowed(self):
        pg_restore_tier_validator('MemoryOptimized', 'GeneralPurpose', SKU_INFO)

    def test_same_tier_is_allowed(self):
        pg_restore_tier_validator('GeneralPurpose', 'GeneralPurpose', SKU_INFO)

    def test_downgrading_tier_is_rejected(self):
        with self.assertRaises(ValidationError) as context:
            pg_restore_tier_validator('GeneralPurpose', 'MemoryOptimized', SKU_INFO)
        self.assertIn('must not go below the source server compute tier', str(context.exception))

    def test_downgrading_to_burstable_is_rejected(self):
        with self.assertRaises(ValidationError):
            pg_restore_tier_validator('Burstable', 'GeneralPurpose', SKU_INFO)

    def test_unknown_tier_is_rejected(self):
        with self.assertRaises(Exception) as context:
            pg_restore_tier_validator('NotATier', 'GeneralPurpose', SKU_INFO)
        self.assertIn('Invalid value for --tier', str(context.exception))


if __name__ == '__main__':
    unittest.main()
