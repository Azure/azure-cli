# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.command_modules.acs import _helpers as helpers


class TestPopulateApiServerAccessProfile(unittest.TestCase):
    def test_single_cidr_with_spaces(self):
        api_server_authorized_ip_ranges = "0.0.0.0/32 "
        profile = helpers._populate_api_server_access_profile(api_server_authorized_ip_ranges)
        self.assertListEqual(profile.authorized_ip_ranges, ["0.0.0.0/32"])

    def test_multi_cidr_with_spaces(self):
        api_server_authorized_ip_ranges = " 0.0.0.0/32 , 129.1.1.1/32"
        profile = helpers._populate_api_server_access_profile(api_server_authorized_ip_ranges)
        self.assertListEqual(profile.authorized_ip_ranges, ["0.0.0.0/32", "129.1.1.1/32"])
