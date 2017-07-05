# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import os

from azure.cli.core.commands.progress import ProgressReporter, ProgressHook

import azclishell.progress as prog


class ShellProgressViewTest(unittest.TestCase):
    def init(self):
        self.model = ProgressReporter()
        self.view = prog.ShellProgressView()
        self.controller = ProgressHook()
        self.controller.reporter = self.model
        self.controller.init_progress(self.view)

    def test_shell_progress_write(self):
        self.init()
        self.controller.add(message='Test1')
        self.assertEqual(prog.get_progress_message(), 'Test1')
        self.assertEqual(prog.PROGRESS_BAR, "")

    @unittest.skipIf(os.getenv('TERM') is None, 'Skip when $TERM is missing')
    def test_shell_progress_write_2(self):
        self.init()
        self.controller.add(message='Test2', total_val=10, value=1)
        self.assertEqual(prog.get_progress_message(), 'Test2')
        self.assertTrue(prog.PROGRESS_BAR is not None)


if __name__ == '__main__':
    unittest.main()
