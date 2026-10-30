# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import unittest
from types import SimpleNamespace

from azure.mgmt.sql.models import ManagedInstance

from azure.cli.command_modules.sql import SqlCommandsLoader
from azure.cli.command_modules.sql._util import build_sdk_model
from azure.cli.core.mock import DummyCli


class SqlManagedInstanceMemoryArgumentTest(unittest.TestCase):
    # SQL SDK 5.0 preserves Python scalar types instead of applying msrest's integer coercion.

    def test_create_and_update_serialize_memory_as_a_json_integer(self):
        for command in ('sql mi create', 'sql mi update'):
            with self.subTest(command=command):
                cli = DummyCli()
                cli.invocation = SimpleNamespace(data={'command_string': command})
                loader = SqlCommandsLoader(cli)
                loader.load_command_table(command.split())
                loader.load_arguments(command)
                argument = loader.argument_registry.get_cli_argument(command, 'memory_size_in_gb')
                parser = argparse.ArgumentParser(exit_on_error=False)
                parser.add_argument(
                    *argument.settings['options_list'], dest='memory_size_in_gb',
                    type=argument.settings.get('type', str))

                namespace = parser.parse_args(['--memory', '64'])
                model = build_sdk_model(ManagedInstance, vars(namespace))
                memory = model.as_dict()['properties']['memorySizeInGB']

                self.assertIsInstance(memory, int)
                self.assertEqual(memory, 64)
                with self.assertRaises(argparse.ArgumentError):
                    parser.parse_args(['--memory', '64.5'])
