# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from azure.cli.command_modules.network.zone_file import parse_zone_file

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class TestDnsZoneImport(unittest.TestCase):

    def _check_soa(self, zone, ttl, serial_number, refresh, retry, expire, min_ttl):
        self.assertEqual(zone['@']['soa'][0]['ttl'], ttl)
        self.assertEqual(zone['@']['soa'][0]['serial'], serial_number)
        self.assertEqual(zone['@']['soa'][0]['refresh'], refresh)
        self.assertEqual(zone['@']['soa'][0]['retry'], retry)
        self.assertEqual(zone['@']['soa'][0]['expire'], expire)
        self.assertEqual(zone['@']['soa'][0]['minimum'], min_ttl)

    def _check_ns(self, zone, name, records_to_check):
        for i, record in enumerate(zone[name]['ns']):
            self.assertEqual(record['ttl'], records_to_check[i][0])
            self.assertEqual(record['host'], records_to_check[i][1])

    def _check_mx(self, zone, name, records_to_check):
        for i, record in enumerate(zone[name]['mx']):
            self.assertEqual(record['ttl'], records_to_check[i][0])
            self.assertEqual(int(record['preference']), records_to_check[i][1])
            self.assertEqual(record['host'], records_to_check[i][2])

    def _check_a(self, zone, name, records_to_check):
        for i, record in enumerate(zone[name]['a']):
            self.assertEqual(record['ttl'], records_to_check[i][0])
            self.assertEqual(record['ip'], records_to_check[i][1])

    def _check_aaaa(self, zone, name, records_to_check):
        for i, record in enumerate(zone[name]['aaaa']):
            self.assertEqual(record['ttl'], records_to_check[i][0])
            self.assertEqual(record['ip'], records_to_check[i][1])

    def _check_cname(self, zone, name, records_to_check):
        for i, record in enumerate(zone[name]['cname']):
            self.assertEqual(record['ttl'], records_to_check[i][0])
            self.assertEqual(record['alias'], records_to_check[i][1])

    def _check_ptr(self, zone, name, records_to_check):
        for i, record in enumerate(zone[name]['ptr']):
            self.assertEqual(record['ttl'], records_to_check[i][0])
            self.assertEqual(record['host'], records_to_check[i][1])

    def _check_txt(self, zone, name, records_to_check):
        for i, record in enumerate(zone[name]['txt']):
            self.assertEqual(record['ttl'], records_to_check[i][0])
            for txt_entry in record['txt']:
                self.assertLessEqual(len(txt_entry), 255)
            long_txt = ''.join(record['txt'])
            if records_to_check[i][1]:
                self.assertEqual(len(long_txt), records_to_check[i][1])
            if records_to_check[i][2]:
                self.assertEqual(long_txt, records_to_check[i][2])

    def _check_srv(self, zone, name, records_to_check):
        for i, record in enumerate(zone[name]['srv']):
            self.assertEqual(record['ttl'], records_to_check[i][0])
            self.assertEqual(int(record['priority']), records_to_check[i][1])
            self.assertEqual(int(record['weight']), records_to_check[i][2])
            self.assertEqual(int(record['port']), records_to_check[i][3])
            self.assertEqual(record['target'], records_to_check[i][4])

    def _get_zone_object(self, file_name):
        file_path = os.path.join(TEST_DIR, 'zone_files', file_name)
        file_text = None
        with open(file_path) as f:
            file_text = f.read()
        return parse_zone_file(file_text)

    def test_zone_file_1(self):
        zone = self._get_zone_object('zone1.txt')
        self._check_soa(zone, 3600, 1, 3600, 300, 2419200, 300)
        self._check_ns(zone, '@', [
            (172800, 'ns0-00.azure-dns.com.'),
            (172800, 'ns0-00.azure-dns.net.'),
            (172800, 'ns0-00.azure-dns.org.'),
            (172800, 'ns0-00.azure-dns.info.')
        ])
        self._check_ns(zone, 'myns', [(3600, 'ns.contoso.com')])
        self._check_mx(zone, 'mymx', [(3600, 1, 'mail.contoso.com')])
        self._check_a(zone, 'manuala', [(3600, '10.0.0.10')])
        self._check_a(zone, 'mya', [(0, '10.0.1.0'), (0, '10.0.1.1')])
        self._check_aaaa(zone, 'myaaaa', [(3600, '2001:4898:e0:99:6dc4:6329:1c99:4e69')])
        self._check_cname(zone, 'mycname', [(3600, 'contoso.com')])
        self._check_ptr(zone, 'myname', [(3600, 'myptrdname')])
        self._check_ptr(zone, 'myptr', [(3600, 'contoso.com')])
        self._check_txt(zone, 'myname2', [(3600, 9, 'manualtxt')])
        self._check_txt(zone, 'mytxt2', [(7200, 7, 'abc def'), (7200, 7, 'foo bar')])
        self._check_txt(zone, 'mytxtrs', [(3600, 2, 'hi')])
        self._check_srv(zone, 'mysrv', [(3600, 1, 2, 1234, 'target.contoso.com')])

    def test_zone_file_2(self):
        zone = self._get_zone_object('zone2.txt')
        self._check_soa(zone, 3600, 10, 900, 600, 86400, 3600)

    def test_zone_file_3(self):
        zone = self._get_zone_object('zone3.txt')
        self._check_soa(zone, 86400, 2003080800, 43200, 900, 1814400, 10800)  # should 3600 override 1d or not??

    def test_zone_file_4(self):
        zone = self._get_zone_object('zone4.txt')
        self._check_soa(zone, 3600, 2003080800, 43200, 900, 1814400, 10800)
        self.assertEqual(zone['@']['ns'][0]['ttl'], 100)

    def test_zone_file_5(self):
        zone = self._get_zone_object('zone5.txt')
        self._check_soa(zone, 3600, 2003080800, 43200, 900, 1814400, 10800)

if __name__ == '__main__':
    unittest.main()
