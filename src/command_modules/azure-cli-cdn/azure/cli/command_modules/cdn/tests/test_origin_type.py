# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import argparse
import unittest
from azure.cli.command_modules.cdn._params import OriginType


class OriginTypeTests(unittest.TestCase):

    def setUp(self):
        self.subject = OriginType(None, None)

    def _check_values(self, origin, host_name, http_port, https_port):
        self.assertEqual(origin.host_name, host_name)
        self.assertEqual(origin.http_port, http_port)
        self.assertEqual(origin.https_port, https_port)

    def test_origin_type_just_domain(self):
        values = ['www.domain.com']
        self._check_values(self.subject.get_origin(values, None), values[0], 80, 443)

    def test_origin_type_with_http_port(self):
        values = ['www.domain.com', 300]
        self._check_values(self.subject.get_origin(values, None), values[0], 300, 443)

    def test_origin_type_with_http_and_https_port(self):
        values = ['www.domain.com', 300, 5000]
        self._check_values(self.subject.get_origin(values, None), values[0], 300, 5000)

    def test_origin_too_many_values(self):
        values = ['www.domain.com', 300, 5000, 'bad']
        with self.assertRaises(argparse.ArgumentError):
            self.subject.get_origin(values, None)

    def test_origin_too_few_values(self):
        values = []
        with self.assertRaises(argparse.ArgumentError):
            self.subject.get_origin(values, None)
