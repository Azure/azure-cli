# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import unittest
from io import StringIO

from azure.cli.core.commands.validators import (validate_key_value_pairs, validate_tag,
                                                validate_tags)


class TestStorageValidators(unittest.TestCase):
    def setUp(self):
        self.io = StringIO()

    def tearDown(self):
        self.io.close()

    def test_key_value_pairs_valid(self):
        the_input = 'a=b;c=d'
        actual = validate_key_value_pairs(the_input)
        expected = {'a': 'b', 'c': 'd'}
        self.assertEqual(actual, expected)

    def test_key_value_pairs_invalid(self):
        the_input = 'a=b;c=d;e'
        actual = validate_key_value_pairs(the_input)
        expected = {'a': 'b', 'c': 'd'}
        self.assertEqual(actual, expected)

    def test_tags_valid(self):
        the_input = argparse.Namespace()
        the_input.tags = ['a=b', 'c=d', 'e']
        validate_tags(the_input)
        expected = {'a': 'b', 'c': 'd', 'e': ''}
        self.assertEqual(the_input.tags, expected)

    def test_tags_invalid(self):
        the_input = argparse.Namespace()
        the_input.tags = []
        validate_tags(the_input)
        self.assertEqual(the_input.tags, {})

    def test_tag(self):
        self.assertEqual(validate_tag('test'), {'test': ''})
        self.assertEqual(validate_tag('a=b'), {'a': 'b'})
        self.assertEqual(validate_tag('a=b;c=d'), {'a': 'b;c=d'})


if __name__ == '__main__':
    unittest.main()
