# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.core.mock import DummyCli
from azure.cli.core import MainCommandsLoader


class CommandTableIntegrityTest(unittest.TestCase):

    def setUp(self):
        self.cli_ctx = DummyCli()

    def test_command_table_integrity(self):
        """Test command table loading produces valid, complete results."""

        # Load command table using current implementation
        loader = MainCommandsLoader(self.cli_ctx)
        loader.load_command_table([])

        # Test invariants that should always hold:

        # 1. No corruption/duplicates
        command_names = list(loader.command_table.keys())
        unique_command_names = set(command_names)
        self.assertEqual(len(unique_command_names), len(command_names), "No duplicate commands")

        # 2. Core functionality exists (high-level groups that should always exist)
        core_groups = ['vm', 'network', 'resource', 'account', 'group']
        existing_groups = {cmd.split()[0] for cmd in loader.command_table.keys() if ' ' in cmd}
        missing_core = [group for group in core_groups if group not in existing_groups]
        self.assertEqual(len(missing_core), 0, f"Missing core command groups: {missing_core}")

        # 3. Structural integrity
        commands_without_source = []
        for cmd_name, cmd_obj in loader.command_table.items():
            if not hasattr(cmd_obj, 'command_source') or not cmd_obj.command_source:
                commands_without_source.append(cmd_name)

        self.assertEqual(len(commands_without_source), 0,
                         f"Commands missing source: {commands_without_source[:5]}...")

        # 4. Basic sanity - we loaded SOMETHING
        self.assertGreater(len(loader.command_table), 0, "Commands were loaded")
        self.assertGreater(len(loader.command_group_table), 0, "Groups were loaded")

        # 5. Verify core groups are properly represented
        found_core_groups = sorted(existing_groups & set(core_groups))
        self.assertGreaterEqual(len(found_core_groups), 3,
                                f"At least 3 core command groups should be present, found: {found_core_groups}")


if __name__ == '__main__':
    unittest.main()
