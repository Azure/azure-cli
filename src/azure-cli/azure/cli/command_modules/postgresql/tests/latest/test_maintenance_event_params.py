# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from knack.arguments import IgnoreAction
from azure.cli.core.mock import DummyCli
from azure.cli.command_modules.postgresql import PostgreSQLCommandsLoader


def _load_command_and_arguments(command):
    """Load the PostgreSQL command loader for *command* and return the loader."""
    cli = DummyCli(commands_loader_cls=PostgreSQLCommandsLoader)
    loader = PostgreSQLCommandsLoader(cli)
    cli.invocation = mock.MagicMock()
    cli.invocation.commands_loader = loader
    loader.command_name = command
    loader.load_command_table(None)
    loader.load_arguments(command)
    loader._update_command_definitions()
    return loader


class MaintenanceEventParamsTest(unittest.TestCase):
    """Regression test for https://github.com/Azure/azure-cli/issues/33846.

    `az postgres flexible-server maintenance-event list` does not accept an `ids`
    keyword argument in its custom command implementation, so the auto-generated
    `--ids` argument must be ignored for that command. Otherwise, invoking the
    command with `--ids` results in a TypeError.
    """

    def test_maintenance_event_list_ignores_ids(self):
        """The ``ids`` argument for the list command must use IgnoreAction."""
        loader = _load_command_and_arguments(
            'postgres flexible-server maintenance-event list'
        )
        ids_arg = loader.argument_registry.arguments.get(
            'postgres flexible-server maintenance-event list', {}
        ).get('ids')
        self.assertIsNotNone(ids_arg, "'ids' argument not found in argument registry")
        action = ids_arg.settings.get('action')
        self.assertIs(
            action,
            IgnoreAction,
            "Expected 'ids' to be registered with IgnoreAction (via c.ignore('ids')), "
            "but got: {}".format(action),
        )


if __name__ == '__main__':
    unittest.main()

