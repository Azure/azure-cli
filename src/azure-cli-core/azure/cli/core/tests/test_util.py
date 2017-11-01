# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from collections import namedtuple
import unittest
import tempfile
from datetime import date, time, datetime

from azure.cli.core.util import \
    (get_file_json, truncate_text, shell_safe_json_parse, b64_to_hex, hash_string, random_string)


class TestUtils(unittest.TestCase):

    def test_load_json_from_file(self):
        _, pathname = tempfile.mkstemp()

        # test good case
        with open(pathname, 'w') as good_file:
            good_file.write('{"key1":"value1", "key2":"value2"}')
        result = get_file_json(pathname)
        self.assertEqual('value2', result['key2'])

        # test error case
        with open(pathname, 'w') as bad_file:
            try:
                bad_file.write('{"key1":"value1" "key2":"value2"}')
                get_file_json(pathname)
                self.fail('expect throw on reading from badly formatted file')
            except Exception as ex:  # pylint: disable=broad-except
                self.assertTrue(str(ex).find(
                    'contains error: Expecting value: line 1 column 1 (char 0)'))

    def test_truncate_text(self):
        expected = 'stri [...]'
        actual = truncate_text('string to shorten', width=10)
        self.assertEqual(expected, actual)

    def test_truncate_text_not_needed(self):
        expected = 'string to shorten'
        actual = truncate_text('string to shorten', width=100)
        self.assertEqual(expected, actual)

    def test_truncate_text_zero_width(self):
        with self.assertRaises(ValueError):
            truncate_text('string to shorten', width=0)

    def test_truncate_text_negative_width(self):
        with self.assertRaises(ValueError):
            truncate_text('string to shorten', width=-1)

    def test_shell_safe_json_parse(self):
        dict_obj = {'a': 'b & c'}
        list_obj = [{'a': 'b & c'}]
        failed_strings = []

        valid_dict_strings = [
            '{"a": "b & c"}',
            "{'a': 'b & c'}",
            "{\"a\": \"b & c\"}"
        ]
        for string in valid_dict_strings:
            actual = shell_safe_json_parse(string)
            try:
                self.assertEqual(actual, dict_obj)
            except AssertionError:
                failed_strings.append(string)

        valid_list_strings = [
            '[{"a": "b & c"}]',
            "[{'a': 'b & c'}]",
            "[{\"a\": \"b & c\"}]"
        ]
        for string in valid_list_strings:
            actual = shell_safe_json_parse(string)
            try:
                self.assertEqual(actual, list_obj)
            except AssertionError:
                failed_strings.append(string)

        self.assertEqual(
            len(failed_strings), 0,
            'The following patterns failed: {}'.format(failed_strings))

    def test_hash_string(self):
        def _run_test(length, force_lower):
            import random
            # test a bunch of random strings for collisions
            test_values = []
            for x in range(100):
                rand_len = random.randint(50, 100)
                test_values.append(random_string(rand_len))

            # test each value against eachother to verify hashing properties
            equal_count = 0
            for val1 in test_values:
                result1 = hash_string(val1, length, force_lower)

                # test against the remaining values and against itself, but not those which have
                # come before...
                test_values2 = test_values[test_values.index(val1):]
                for val2 in test_values2:
                    result2 = hash_string(val2, length, force_lower)
                    if val1 == val2:
                        self.assertEqual(result1, result2)
                        equal_count += 1
                    else:
                        self.assertNotEqual(result1, result2)
            self.assertEqual(equal_count, len(test_values))

        # Test digest replication
        _run_test(100, False)

        # Test force_lower
        _run_test(16, True)


class TestBase64ToHex(unittest.TestCase):

    def setUp(self):
        self.base64 = 'PvOJgaPq5R004GyT1tB0IW3XUyM='.encode('ascii')

    def test_b64_to_hex(self):
        self.assertEquals('3EF38981A3EAE51D34E06C93D6D074216DD75323', b64_to_hex(self.base64))

    def test_b64_to_hex_type(self):
        self.assertIsInstance(b64_to_hex(self.base64), str)


if __name__ == '__main__':
    unittest.main()
