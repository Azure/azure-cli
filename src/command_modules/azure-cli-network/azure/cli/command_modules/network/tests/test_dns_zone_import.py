# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from azure.cli.command_modules.network.zone_file import parse_zone_file

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class TestDnsZoneImport(unittest.TestCase):

    def _get_zone_object(self, file_name):
        file_path = os.path.join(TEST_DIR, 'zone_files', file_name)
        file_text = None
        with open(file_path) as f:
            file_text = f.read()
        return parse_zone_file(file_text)

    def test_zone_file_1(self):
        zone = self._get_zone_object('zone1.txt')
        # TODO verify unique properties here

    def test_zone_file_2(self):
        zone = self._get_zone_object('zone2.txt')
        # TODO verify unique properties here

    def test_zone_file_3(self):
        zone = self._get_zone_object('zone3.txt')
        # TODO verify unique properties here

    def test_zone_file_4(self):
        zone = self._get_zone_object('zone4.txt')
        self.assertEqual(zone['@']['soa'][0]['minimum'], 10800)
        self.assertEqual(zone['@']['ns'][0]['ttl'], 100)

    def test_zone_file_5(self):
        zone = self._get_zone_object('zone5.txt')
        # TODO verify unique properties here

if __name__ == '__main__':
    unittest.main()
