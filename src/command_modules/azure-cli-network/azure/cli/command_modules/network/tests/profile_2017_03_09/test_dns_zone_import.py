# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from azure.cli.command_modules.network.zone_file import parse_zone_file

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class TestDnsZoneImport(unittest.TestCase):
    def _check_soa(self, zone, zone_name, ttl, serial_number, refresh, retry, expire, min_ttl):
        record = zone[zone_name]['soa']
        self.assertEqual(record['ttl'], ttl)
        self.assertEqual(record['serial'], serial_number)
        self.assertEqual(record['refresh'], refresh)
        self.assertEqual(record['retry'], retry)
        self.assertEqual(record['expire'], expire)
        self.assertEqual(record['minimum'], min_ttl)

    def _check_ns(self, zone, name, records_to_check):
        self.assertEqual(len(records_to_check), len(zone[name]['ns']))
        for i, record in enumerate(zone[name]['ns']):
            self.assertEqual(record['ttl'], records_to_check[i][0])
            self.assertEqual(record['host'], records_to_check[i][1])

    def _check_mx(self, zone, name, records_to_check):
        self.assertEqual(len(records_to_check), len(zone[name]['mx']))
        for i, record in enumerate(zone[name]['mx']):
            self.assertEqual(record['ttl'], records_to_check[i][0])
            self.assertEqual(int(record['preference']), records_to_check[i][1])
            self.assertEqual(record['host'], records_to_check[i][2])

    def _check_a(self, zone, name, records_to_check):
        self.assertEqual(len(records_to_check), len(zone[name]['a']))
        for i, record in enumerate(zone[name]['a']):
            self.assertEqual(record['ttl'], records_to_check[i][0])
            self.assertEqual(record['ip'], records_to_check[i][1])

    def _check_aaaa(self, zone, name, records_to_check):
        self.assertEqual(len(records_to_check), len(zone[name]['aaaa']))
        for i, record in enumerate(zone[name]['aaaa']):
            self.assertEqual(record['ttl'], records_to_check[i][0])
            self.assertEqual(record['ip'], records_to_check[i][1])

    def _check_caa(self, zone, name, records_to_check):
        self.assertEqual(len(records_to_check), len(zone[name]['caa']))
        for i, record in enumerate(zone[name]['caa']):
            self.assertEqual(record['ttl'], records_to_check[i][0])
            self.assertEqual(record['flags'], records_to_check[i][1])
            self.assertEqual(record['tag'], records_to_check[i][2])
            self.assertEqual(record['value'], records_to_check[i][3])

    def _check_cname(self, zone, name, ttl, alias):
        record = zone[name]['cname']
        self.assertEqual(record['ttl'], ttl)
        self.assertEqual(record['alias'], alias)

    def _check_ptr(self, zone, name, records_to_check):
        self.assertEqual(len(records_to_check), len(zone[name]['ptr']))
        for i, record in enumerate(zone[name]['ptr']):
            self.assertEqual(record['ttl'], records_to_check[i][0])
            self.assertEqual(record['host'], records_to_check[i][1])

    def _check_txt(self, zone, name, records_to_check):
        self.assertEqual(len(records_to_check), len(zone[name]['txt']))
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
        self.assertEqual(len(records_to_check), len(zone[name]['srv']))
        for i, record in enumerate(zone[name]['srv']):
            self.assertEqual(record['ttl'], records_to_check[i][0])
            self.assertEqual(int(record['priority']), records_to_check[i][1])
            self.assertEqual(int(record['weight']), records_to_check[i][2])
            self.assertEqual(int(record['port']), records_to_check[i][3])
            self.assertEqual(record['target'], records_to_check[i][4])

    def _check_ttl(self, zone, name, rec_type, ttl):
        for record in zone[name][rec_type]:
            self.assertEqual(record['ttl'], ttl)

    def _get_zone_object(self, file_name, zone_name):  # pylint: disable=no-self-use
        from azure.cli.core.util import read_file_content
        file_path = os.path.join(TEST_DIR, 'zone_files', file_name)
        file_text = None
        file_text = read_file_content(file_path)
        return parse_zone_file(file_text, zone_name)

    def test_zone_file_1(self):
        zn = 'zone1.com.'
        zone = self._get_zone_object('zone1.txt', zn)
        self._check_soa(zone, zn, 3600, 1, 3600, 300, 2419200, 300)
        self._check_ns(zone, zn, [
            (172800, 'ns0-00.azure-dns.com.'),
            (172800, 'ns0-00.azure-dns.net.'),
            (172800, 'ns0-00.azure-dns.org.'),
            (172800, 'ns0-00.azure-dns.info.')
        ])
        self._check_ns(zone, 'myns.' + zn, [(3600, 'ns.contoso.com.')])
        self._check_mx(zone, 'mymx.' + zn, [(3600, 1, 'mail.contoso.com.')])
        self._check_a(zone, 'manuala.' + zn, [(3600, '10.0.0.10')])
        self._check_a(zone, 'mya.' + zn, [
            (0, '10.0.1.0'),
            (0, '10.0.1.1')
        ])
        self._check_aaaa(zone, 'myaaaa.' + zn, [(3600, '2001:4898:e0:99:6dc4:6329:1c99:4e69')])
        self._check_cname(zone, 'mycname.' + zn, 3600, 'contoso.com.')
        self._check_ptr(zone, 'myname.' + zn, [(3600, 'myptrdname')])
        self._check_ptr(zone, 'myptr.' + zn, [(3600, 'contoso.com')])
        self._check_txt(zone, 'myname2.' + zn, [(3600, 9, 'manualtxt')])
        self._check_txt(zone, 'mytxt2.' + zn, [
            (7200, 7, 'abc def'),
            (7200, 7, 'foo bar')
        ])
        self._check_txt(zone, 'mytxtrs.' + zn, [(3600, 2, 'hi')])
        self._check_srv(zone, 'mysrv.' + zn, [(3600, 1, 2, 1234, 'target.contoso.com.')])
        self._check_caa(zone, 'caa1.' + zn, [
            (60, 0, 'issue', 'ca1.contoso.com'),
            (60, 128, 'iodef', 'mailto:test@contoso.com')
        ])
        self._check_caa(zone, 'caa2.' + zn, [
            (60, 0, 'issue', 'ca1.contoso.com'),
            (60, 45, 'tag56', 'test test test')
        ])

    def test_zone_file_2(self):
        zn = 'mytestzone.com.'
        zone = self._get_zone_object('zone2.txt', zn)
        self._check_txt(zone, 'spaces.' + zn, [(3600, 5, None)])
        self._check_soa(zone, zn, 3600, 10, 900, 600, 86400, 3600)
        self._check_ns(zone, zn, [(3600, 'zoneimport.')])
        self._check_a(zone, 'a2.' + zn, [
            (3600, '1.2.3.4'),
            (3600, '2.3.4.5')
        ])
        self._check_aaaa(zone, 'aaaa2.' + zn, [
            (3600, '2001:cafe:130::100'),
            (3600, '2001:cafe:130::101')
        ])
        self._check_txt(zone, 'doozie.' + zn, [(3600, 108, None)])
        self._check_cname(zone, 'fee2.' + zn, 3600, 'bar.com.')
        self._check_mx(zone, 'mail.' + zn, [
            (3600, 10, 'mail1.mymail.com.'),
            (3600, 11, 'flooble.')
        ])
        self._check_srv(zone, 'sip.tcp.' + zn, [
            (3600, 10, 20, 30, 'foobar.'),
            (3600, 55, 66, 77, 'zoo.')
        ])
        self._check_ns(zone, 'test-ns2.' + zn, [
            (3600, 'ns1.com.'),
            (3600, 'ns2.com.')
        ])
        self._check_txt(zone, 'test-txt2.' + zn, [
            (3600, 8, 'string 1'),
            (3600, 8, 'string 2')
        ])
        self._check_a(zone, 'aa.' + zn, [
            (100, '4.5.6.7'),
            (100, '6.7.8.9')
        ])
        self._check_a(zone, '200.' + zn, [(3600, '7.8.9.0')])
        self._check_mx(zone, 'aa.' + zn, [(300, 1, 'foo.com.' + zn)])
        self._check_txt(zone, 'longtxt2.' + zn, [(100, 500, None)])
        self._check_txt(zone, 'longtxt.' + zn, [(999, 944, None)])
        self._check_txt(zone, 'spf.' + zn, [(100, None, 'this is an SPF record! Convert to TXT on import')])  # pylint: disable=line-too-long
        self._check_txt(zone, zn, [
            (200, None, 'this is another SPF, this time as TXT'),
            (200, None, 'v=spf1 mx ip4:14.14.22.0/23 a:mail.trum.ch mx:mese.ch include:spf.mapp.com ?all')  # pylint: disable=line-too-long
        ])
        self._check_ptr(zone, '160.1.' + zn, [(3600, 'foo.com.')])
        self._check_ptr(zone, '160.2.' + zn, [
            (3600, 'foobar.com.'),
            (3600, 'bar.com.')
        ])
        self._check_ptr(zone, '160.3.' + zn, [
            (3600, 'foo.com.'),
            (3600, 'bar.com.')
        ])
        self._check_txt(zone, 't1.' + zn, [(3600, None, 'foobar')])
        self._check_txt(zone, 't2.' + zn, [(3600, None, 'foobar')])
        self._check_txt(zone, 't3.' + zn, [(3600, None, 'foobar')])
        self._check_txt(zone, 't4.' + zn, [(3600, None, 'foo;bar')])
        self._check_txt(zone, 't5.' + zn, [(3600, None, 'foo\\;bar')])
        self._check_txt(zone, 't6.' + zn, [(3600, None, 'foo\\;bar')])
        self._check_txt(zone, 't7.' + zn, [(3600, None, '\\"quoted string\\"')])
        self._check_txt(zone, 't8.' + zn, [(3600, None, 'foobar')])
        self._check_txt(zone, 't9.' + zn, [(3600, None, 'foobarr')])
        self._check_txt(zone, 't10.' + zn, [(3600, None, 'foo bar')])
        self._check_txt(zone, 't11.' + zn, [(3600, None, 'foobar')])
        self._check_a(zone, 'base.' + zn, [(3600, '194.124.202.114')])
        self._check_mx(zone, 'base.' + zn, [(3600, 10, 'be.xpiler.de.')])
        self._check_txt(zone, 'base.' + zn, [
            (3600, None, 'v=spf1 mx include:_spf4.xcaign.de include:_spf6.xcaign.de -all'),
            (3600, None, 'spf2.0/mfrom,pra mx ip4:15.19.14.0/24 ip4:8.8.11.4/27 ip4:9.16.20.19/26 -all')  # pylint: disable=line-too-long
        ])
        self._check_a(zone, 'even.' + zn, [(3600, '194.124.202.114')])
        self._check_mx(zone, 'even.' + zn, [(3600, 10, 'be.xpiler.de.')])
        self._check_txt(zone, 'even.' + zn, [(3600, None, 'v=spf1 mx include:_spf4.xgn.de include:_spf6.xgn.de -all')])  # pylint: disable=line-too-long

    def test_zone_file_3(self):
        zn = 'example.com.'
        zone = self._get_zone_object('zone3.txt', zn)
        self._check_soa(zone, zn, 86400, 2003080800, 43200, 900, 1814400, 10800)
        self._check_ns(zone, zn, [(86400, 'ns1.com.')])
        self._check_a(zone, 'test-a.' + zn, [(3600, '1.2.3.4')])
        self._check_aaaa(zone, 'test-aaaa.' + zn, [(3600, '2001:cafe:130::100')])
        self._check_cname(zone, 'test-cname.' + zn, 3600, 'target.com.')
        self._check_mx(zone, 'test-mx.' + zn, [(3600, 10, 'mail.com.')])
        self._check_ns(zone, 'test-ns.' + zn, [(3600, 'ns1.com.')])
        self._check_srv(zone, '_sip._tcp.test-srv.' + zn, [(3600, 1, 2, 3, 'target.com.')])
        self._check_txt(zone, 'test-txt.' + zn, [(3600, None, 'string 1')])
        self._check_a(zone, 'd1.' + zn, [
            (3600, '12.1.2.3'),
            (3600, '12.2.3.4'),
            (3600, '12.3.4.5'),
            (3600, '12.4.5.6')
        ])
        self._check_ns(zone, 'd1.' + zn, [(3600, 'hood.com.')])
        self._check_txt(zone, 'd1.' + zn, [(3600, None, 'fishfishfish')])
        self._check_a(zone, 'f1.' + zn, [
            (3600, '11.1.2.3'),
            (3600, '11.2.3.3')
        ])
        self._check_a(zone, 'f2.' + zn, [
            (3600, '11.2.3.4'),
            (3600, '11.5.6.7')
        ])
        self._check_srv(zone, '_sip._tcp.' + zn, [(3600, 10, 20, 30, 'foo.com.')])
        self._check_mx(zone, 'mail.' + zn, [(3600, 100, 'mail.test.com.')])
        self._check_a(zone, 'noclass.' + zn, [
            (3600, '1.2.3.4'),
            (3600, '2.3.4.5')
        ])
        self._check_txt(zone, 'txt1.' + zn, [(3600, None, 'string 1 only')])
        self._check_txt(zone, 'txt2.' + zn, [(3600, None, 'string1string2')])
        self._check_txt(zone, 'txt3.' + zn, [
            (3600, 296, None),
            (3600, None, 'string;string;string')
        ])

    def test_zone_file_4(self):
        zn = 'example.com.'
        zone = self._get_zone_object('zone4.txt', zn)
        self._check_soa(zone, zn, 3600, 2003080800, 43200, 900, 1814400, 10800)
        self._check_ns(zone, zn, [(100, 'ns1.' + zn)])
        self._check_ttl(zone, 'ttl-300.' + zn, 'a', 300)
        self._check_ttl(zone, 'ttl-0.' + zn, 'a', 0)
        self._check_ttl(zone, 'ttl-60.' + zn, 'a', 60)
        self._check_ttl(zone, 'ttl-1w.' + zn, 'a', 604800)
        self._check_ttl(zone, 'ttl-1d.' + zn, 'a', 86400)
        self._check_ttl(zone, 'ttl-1h.' + zn, 'a', 3600)
        self._check_ttl(zone, 'ttl-99s.' + zn, 'a', 99)
        self._check_ttl(zone, 'ttl-100.' + zn, 'a', 100)
        self._check_ttl(zone, 'ttl-6m.' + zn, 'a', 360)
        self._check_ttl(zone, 'ttl-mix.' + zn, 'a', 788645)
        self._check_ttl(zone, 'xttl-1w.' + zn, 'a', 604800)
        self._check_ttl(zone, 'xttl-1d.' + zn, 'a', 86400)
        self._check_ttl(zone, 'xttl-1h.' + zn, 'a', 3600)
        self._check_ttl(zone, 'xttl-99s.' + zn, 'a', 99)
        self._check_ttl(zone, 'xttl-100.' + zn, 'a', 100)
        self._check_ttl(zone, 'xttl-6m.' + zn, 'a', 360)
        self._check_ttl(zone, 'xttl-mix.' + zn, 'a', 788645)
        self._check_a(zone, 'c1.' + zn, [
            (10, '11.1.2.3'),
            (10, '11.2.3.3')
        ])
        self._check_a(zone, 'c2.' + zn, [
            (5, '11.2.3.4'),
            (5, '11.5.6.7')
        ])

    def test_zone_file_5(self):
        zn = 'example.com.'
        zone = self._get_zone_object('zone5.txt', zn)
        self._check_soa(zone, zn, 3600, 2003080800, 43200, 900, 1814400, 10800)
        self._check_a(zone, 'default.' + zn, [(3600, '0.1.2.3')])
        self._check_cname(zone, 'tc.' + zn, 3600, 'test.' + zn)
        self._check_a(zone, zn, [(3600, '1.2.3.4')])
        self._check_a(zone, 'www.' + zn, [(3600, '2.3.4.5')])
        self._check_cname(zone, 'test-cname.' + zn, 3600, 'r1.' + zn)
        self._check_mx(zone, 'test-mx.' + zn, [(3600, 10, 'm1.' + zn)])
        self._check_ns(zone, 'test-ns.' + zn, [(3600, 'ns1.' + zn)])
        self._check_srv(zone, 'test-srv.' + zn, [(3600, 1, 2, 3, 'srv1.' + zn)])
        self._check_cname(zone, 'test-cname2.' + zn, 3600, 'r1.')
        self._check_mx(zone, 'test-mx2.' + zn, [(3600, 10, 'm1.')])
        self._check_ns(zone, 'test-ns2.' + zn, [(3600, 'ns1.')])
        self._check_srv(zone, 'test-srv2.' + zn, [(3600, 1, 2, 3, 'srv1.')])
        self._check_a(zone, 'subzone.' + zn, [(3600, '3.4.5.6')])
        self._check_a(zone, 'www.subzone.' + zn, [(3600, '4.5.6.7')])
        self._check_cname(zone, 'test-cname.subzone.' + zn, 3600, 'r1.subzone.' + zn)
        self._check_cname(zone, 'record.' + zn, 3600, 'bar.foo.com.')
        self._check_a(zone, 'test.' + zn, [(3600, '7.8.9.0')])

    def test_zone_import_errors(self):
        from knack.util import CLIError
        for f in ['fail1', 'fail2', 'fail3', 'fail4', 'fail5']:
            with self.assertRaises(CLIError):
                self._get_zone_object('{}.txt'.format(f), 'example.com')


if __name__ == '__main__':
    unittest.main()
