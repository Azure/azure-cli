# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azclishell.__main__ import AZCOMPLETER, AzLexer, APPLICATION
from azclishell.app import Shell


class ShellRun(unittest.TestCase):
    """ tests whether the shell runs """

    def test_run(self):
        """ tests the running """
        pass
        # self.shell_app = Shell(
        #     completer=AZCOMPLETER,
        #     lexer=AzLexer,
        #     app=APPLICATION,
        # )


if __name__ == '__main__':
    unittest.main()
