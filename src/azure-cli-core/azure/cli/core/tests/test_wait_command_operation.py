# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from knack.util import CLIError

from azure.cli.core.commands.command_operation import WaitCommandOperation
from azure.cli.core.mock import DummyCli


class TestWaitCommandOperationTimeout(unittest.TestCase):

    def test_wait_raises_on_timeout(self):
        """wait() should raise CLIError on timeout, not return it."""
        cli_ctx = DummyCli()

        # A getter that always returns an instance with no satisfied condition
        instance = mock.MagicMock()
        instance.provisioning_state = None
        getter = mock.MagicMock(return_value=instance)

        command_args = {
            'timeout': 1,
            'interval': 1,
            'created': False,
            'deleted': False,
            'updated': False,
            'exists': False,
            'custom': 'nonExistentProperty',
        }

        with self.assertRaises(CLIError) as ctx:
            WaitCommandOperation.wait(command_args, cli_ctx=cli_ctx, getter=getter)

        self.assertIn('timed-out', str(ctx.exception))

    def test_wait_returns_none_on_success(self):
        """wait() should return None when the condition is satisfied."""
        cli_ctx = DummyCli()

        # exists=True causes immediate return without inspecting provisioning_state
        getter = mock.MagicMock(return_value=mock.MagicMock())

        command_args = {
            'timeout': 30,
            'interval': 1,
            'created': False,
            'deleted': False,
            'updated': False,
            'exists': True,
            'custom': None,
        }

        result = WaitCommandOperation.wait(command_args, cli_ctx=cli_ctx, getter=getter)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
