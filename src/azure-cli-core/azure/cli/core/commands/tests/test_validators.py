# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import os

from azure.cli.core.commands.validators import validate_file_or_dict, JSON_RECOMMENDATION_MESSAGE
from azure.cli.core.azclierror import InvalidArgumentValueError


class TestValidators(unittest.TestCase):

    def test_validate_file_or_dict(self):
        json_str = '{"name": "my-resource"}'
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        temp_file = os.path.join(curr_dir, 'temp.json')

        # Parse JSON file
        with open(temp_file, 'w') as f:
            f.write(json_str)
        json_read = validate_file_or_dict(temp_file)
        assert json_read['name'] == 'my-resource'
        os.remove(temp_file)

        # Parse in-line JSON string
        json_read = validate_file_or_dict(json_str)
        assert json_read['name'] == 'my-resource'

        # Test error 1: Parse JSON file with error
        with open(temp_file, 'w') as f:
            f.write(json_str)
            f.write('error!')
        with self.assertRaisesRegex(InvalidArgumentValueError, 'Failed to parse file') as ex:
            validate_file_or_dict(temp_file)
        assert ex.exception.recommendations[0] == JSON_RECOMMENDATION_MESSAGE
        assert len(ex.exception.recommendations) == 1
        os.remove(temp_file)

        # Test error 2: A non-existing file, but it looks like a JSON file
        with self.assertRaisesRegex(InvalidArgumentValueError, 'JSON file does not exist') as ex:
            validate_file_or_dict("not-exist.json")
        assert ex.exception.recommendations[0] == JSON_RECOMMENDATION_MESSAGE
        assert len(ex.exception.recommendations) == 1

        # Test error 3: A non-existing file, or invalid JSON string
        with self.assertRaisesRegex(InvalidArgumentValueError, 'Failed to parse string as JSON') as ex:
            validate_file_or_dict("invalid-string")
        assert ex.exception.recommendations[0] == JSON_RECOMMENDATION_MESSAGE
        assert 'The provided JSON string may have been parsed by the shell.' in ex.exception.recommendations[1]


if __name__ == '__main__':
    unittest.main()
