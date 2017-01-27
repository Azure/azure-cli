# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from azure.cli.command_modules.network.zone_file import parse_zone_file

class TestDnsZoneImport(unittest.TestCase):

    def test_zone_file_1(self):

        file_path = os.path.join(TEST_DIR, 'zone_files', 'zone1.txt')
        file_text = None
        with open(file_path) as f:
            file_text = f.read()
        zone = parse_zone_file(file_text)


if __name__ == '__main__':
    unittest.main()
