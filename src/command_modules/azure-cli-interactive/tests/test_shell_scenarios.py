# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import tempfile
import os
import unittest


class ShellScenarioTest(unittest.TestCase):
    """ tests whether dump commands works """
    def __init__(self, *args, **kwargs):
        super(ShellScenarioTest, self).__init__(*args, **kwargs)

    def test_install_modules(self):
        """ tests the running """
        pass


if __name__ == '__main__':
    unittest.main()
