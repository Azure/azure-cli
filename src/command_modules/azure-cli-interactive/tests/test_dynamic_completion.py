# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import six
import sys

from prompt_toolkit.document import Document

from azclishell.__main__ import AZCOMPLETER


class DynamicShellCompletionsTest(unittest.TestCase):

    def test_mute_parse(self):
        """ tests dynamic completions """
        completer = AZCOMPLETER

        stream = six.StringIO()
        sys.stderr = stream
        completer.argsfinder.set_outstream(stream)
        completer.argsfinder.get_parsed_args(['this', 'is', 'world'])
        self.assertTrue(stream.getvalue() == '')


if __name__ == '__main__':
    unittest.main()
