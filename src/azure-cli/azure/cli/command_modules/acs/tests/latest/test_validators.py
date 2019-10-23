# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import mock
from azure.cli.core.util import CLIError
from azure.cli.command_modules.acs import _validators as validators


class TestValidateIPRanges(unittest.TestCase):
    def test_simultaneous_allow_and_disallow_with_spaces(self):
        api_server_authorized_ip_ranges = " 0.0.0.0/32 , 129.1.1.1.1 "
        namespace = Namespace(api_server_authorized_ip_ranges)
        err = "--api-server-authorized-ip-ranges cannot restrict traffic via 0.0.0.0/32 and \
            simultaneously enable traffic by setting other IPv4 addresses or CIDRs"
        self.assertRaisesRegex(CLIError, err, validators.validate_ip_ranges, namespace)


    def test_simultaneous_enable_and_disable_with_spaces(self):
        # an entry of "", 129.1.1.1.1 from command line is translated into " , 129.1.1.1.1"
        api_server_authorized_ip_ranges = " , 129.1.1.1.1"
        namespace = Namespace(api_server_authorized_ip_ranges)
        err = "--api-server-authorized-ip-ranges cannot be disabled and simultaneously enabled"
        self.assertRaisesRegex(CLIError, err, validators.validate_ip_ranges, namespace)


    def test_disable_authorized_ip_ranges(self):
        api_server_authorized_ip_ranges = ''
        namespace = Namespace(api_server_authorized_ip_ranges)
        validators.validate_ip_ranges(namespace)


    def test_local_ip_address(self):
        api_server_authorized_ip_ranges = "192.168.0.0,192.168.0.0/16"
        namespace = Namespace(api_server_authorized_ip_ranges)
        err = "--api-server-authorized-ip-ranges must be global non-reserved addresses or CIDRs"
        self.assertRaisesRegex(CLIError, err, validators.validate_ip_ranges, namespace)
    
    def test_invalid_ip(self):
        api_server_authorized_ip_ranges = "193.168.0"
        namespace = Namespace(api_server_authorized_ip_ranges)
        err = "--api-server-authorized-ip-ranges should be a list of IPv4 addresses or CIDRs"
        self.assertRaisesRegex(CLIError, err, validators.validate_ip_ranges, namespace)
    
    def test_IPv6(self):
        api_server_authorized_ip_ranges = "3ffe:1900:4545:3:200:f8ff:fe21:67cf"
        namespace = Namespace(api_server_authorized_ip_ranges)
        err = "--api-server-authorized-ip-ranges cannot be IPv6 addresses"
        self.assertRaisesRegex(CLIError, err, validators.validate_ip_ranges, namespace)


class Namespace:
    def __init__(self, api_server_authorized_ip_ranges):
        self.api_server_authorized_ip_ranges = api_server_authorized_ip_ranges