# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest import mock
from azure.cli.command_modules.cdn._validators import validate_origin
from knack.util import CLIError


class ValidatorTests(unittest.TestCase):
    def test_validate_origin_passes_on_empty(self):
        namespace = mock.MagicMock()
        self.assertEqual(validate_origin(namespace), True)

    def test_validate_origin_on_http_port_range_high(self):
        namespace = mock.MagicMock()
        origin = mock.MagicMock()
        origin.http_port = 65537
        namespace.origins = [origin]
        with self.assertRaises(CLIError):
            validate_origin(namespace)

    def test_validate_raise_on_https_port_range_high(self):
        namespace = mock.MagicMock()
        origin = mock.MagicMock()
        origin.http_port = 80
        origin.https_port = 65537
        namespace.origins = [origin]
        with self.assertRaises(CLIError):
            validate_origin(namespace)

    def test_validate_raise_on_http_port_range_low(self):
        namespace = mock.MagicMock()
        origin = mock.MagicMock()
        origin.http_port = -1
        origin.https_port = 443
        namespace.origins = [origin]
        with self.assertRaises(CLIError):
            validate_origin(namespace)

    def test_validate_raise_on_https_port_range_low(self):
        namespace = mock.MagicMock()
        origin = mock.MagicMock()
        origin.http_port = 80
        origin.https_port = -443
        namespace.origins = [origin]
        with self.assertRaises(CLIError):
            validate_origin(namespace)
