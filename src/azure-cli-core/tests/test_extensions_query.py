# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.core.extensions.query import jmespath_type


class TestQuery(unittest.TestCase):
    '''Tests for the values that can be passed to the --query parameter.
    These tests ensure that we are handling invalid queries correctly and raising appropriate errors
    that argparse can then handle.
    (We are not testing JMESPath itself here.)
    '''

    def test_query_valid_1(self):  # pylint: disable=no-self-use
        query = 'length(@)'
        # Should not raise any exception as it is valid
        jmespath_type(query)

    def test_query_valid_2(self):  # pylint: disable=no-self-use
        query = "[?storageProfile.osDisk.osType=='Linux'].[resourceGroup,name]"
        # Should not raise any exception as it is valid
        jmespath_type(query)

    def test_query_empty(self):
        query = ''
        with self.assertRaises(ValueError):
            jmespath_type(query)

    def test_query_unbalanced(self):
        query = 'length(@'
        with self.assertRaises(ValueError):
            jmespath_type(query)

    def test_query_invalid_1(self):
        query = '[?asdf=asdf]'
        with self.assertRaises(ValueError):
            jmespath_type(query)

    def test_query_invalid_2(self):
        query = '[?name=My Resource Group]'
        with self.assertRaises(ValueError):
            jmespath_type(query)

    def test_query_invalid_3(self):
        query = "[].location='westus'"
        with self.assertRaises(ValueError):
            jmespath_type(query)

    def test_query_invalid_4(self):
        query = "length([?contains('id', 'Publishers'])"
        with self.assertRaises(ValueError):
            jmespath_type(query)


if __name__ == '__main__':
    unittest.main()
