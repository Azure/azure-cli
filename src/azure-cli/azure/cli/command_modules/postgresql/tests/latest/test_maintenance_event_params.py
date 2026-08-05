# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import inspect
import unittest

from azure.cli.command_modules.postgresql._params import load_arguments


class MaintenanceEventParamsTest(unittest.TestCase):
    """Regression test for https://github.com/Azure/azure-cli/issues/33846.

    `az postgres flexible-server maintenance-event list` does not accept an `ids`
    keyword argument in its custom command implementation, so the auto-generated
    `--ids` argument must be ignored for that command. Otherwise, invoking the
    command with `--ids` results in a TypeError.
    """

    def test_maintenance_event_list_ignores_ids(self):
        source = inspect.getsource(load_arguments)
        list_context_index = source.index("flexible-server maintenance-event list")
        # the ignore('ids') call should immediately follow the list argument context
        snippet = source[list_context_index:list_context_index + 300]
        self.assertIn("c.ignore('ids')", snippet)


if __name__ == '__main__':
    unittest.main()
