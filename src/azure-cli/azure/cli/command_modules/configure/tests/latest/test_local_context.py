# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
import tempfile

from azure.cli.testsdk import ScenarioTest
from knack.util import CLIError


class LocalContextTest(ScenarioTest):
    def test_local_context_on_off(self):
        original_working_dir = os.getcwd()
        working_dir = tempfile.mkdtemp()
        os.chdir(working_dir)
        self.cmd('local-context on')
        self.cmd('local-context off --yes')
        os.chdir(original_working_dir)


if __name__ == '__main__':
    unittest.main()
