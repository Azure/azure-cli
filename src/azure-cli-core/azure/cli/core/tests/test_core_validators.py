# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import unittest
import os
import tempfile

from azure.cli.core.commands.validators import validate_file_or_dict


class TestValidators(unittest.TestCase):

    def test_validate_file_or_dict(self):
        # verify user folder is expanded before load the file
        temp_name = next(tempfile._get_candidate_names())
        file_path = '~/' + temp_name
        local_file_path = os.path.expanduser(file_path)
        with open(local_file_path, 'w') as f:
            f.write('{"prop":"val"}')

        # verify we load the json content correctly
        try:
            res = validate_file_or_dict(file_path)
            self.assertEqual(res['prop'], "val")
        finally:
            os.remove(local_file_path)

        # verify expanduser call won't mess up the json data
        data = '{"~d": "~/haha"}'
        res = validate_file_or_dict(data)
        self.assertEqual(res['~d'], '~/haha')

        # verify expanduser call again, but use single quot
        data = "{'~d': '~/haha'}"
        res = validate_file_or_dict(data)
        self.assertEqual(res['~d'], '~/haha')


if __name__ == '__main__':
    unittest.main()
