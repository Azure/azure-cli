# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import print_function
import unittest
import sys
import six

from prompt_toolkit.document import Document

from azclishell.__main__ import AZCOMPLETER


class DynamicShellCompletionsTest(unittest.TestCase):

    def test_mute_parse(self):
        """ tests dynamic completions """
        completer = AZCOMPLETER
        stream = six.StringIO()

        # stderr = sys.stderr
        # sys.stderr = stream
        # completer.get_completions(
        #     Document(u'vm create -g '), None)
        # self.assertTrue(stream.getvalue() == '')

        # sys.stderr = stderr


if __name__ == '__main__':
    unittest.main()
