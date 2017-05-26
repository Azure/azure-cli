# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import six
from azclishell.app import Shell


class QueryInjection(unittest.TestCase):
    """ tests using the query gesture for the interactive mode """
    def __init__(self):
        super(QueryInjection, self).__init__()
        self.stream = six.StringIO()
        self.shell = Shell(output_custom=self.stream)
        self.shell.cli_execute = 

    def test_null(self):
        """ tests neutral case """
        args = ['']
        self.shell.handle_jmespath_query(args, True)

    def test_just_query(self):
        """ tests flushing just the query """

    def test_replacement(self):
        """ tests that the query replaces the values in the command """

    def test_quotes(self):
        """ tests that it parses correctly with quotes in the command """

    def test_generic_example(self):


if __name__ == '__main__':
    unittest.main()
