# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import six
from azclishell.util import parse_quotes
import unittest


class ParseTest(unittest.TestCase):

    def test_parse_quotes(self):
        cmd1 = 'account set --subscription \'Visual Studeio enterprizse (msft)\''
        args1 = parse_quotes(cmd1)
        self.assertEqual(
            args1, ['account', 'set', '--subscription', 'Visual Studeio enterprizse (msft)'])

        cmd2 = 'account set --subscription \"Visual Studeio enterprizse (msft)\"'
        args2 = parse_quotes(cmd2)
        self.assertEqual(
            args2, ['account', 'set', '--subscription', 'Visual Studeio enterprizse (msft)'])

        cmd3 = 'account set --subscription'
        args3 = parse_quotes(cmd3)
        self.assertEqual(args3, ['account', 'set', '--subscription'])

        cmd4 = 'word1 "quote1" word2 "quote is 3" words are fun'
        args4 = parse_quotes(cmd4)
        self.assertEqual(
            args4, ['word1', "quote1", 'word2', "quote is 3", 'words', 'are', 'fun'])

        cmd5 = '"??[?resourceGroup == "CJ101"].name"'
        args5 = parse_quotes(cmd5)
        self.assertEqual(
            args5, ['??[?resourceGroup == CJ101].name']
        )


if __name__ == '__main__':
    unittest.main()
