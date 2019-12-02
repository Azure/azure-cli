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


class TestSetVmSetType(unittest.TestCase):
    def test_archaic_k8_version(self):
        version = "1.11.9"
        vm_type = helpers._set_vm_set_type("", version)
        self.assertEqual(vm_type, "AvailabilitySet")

    def test_archaic_k8_version_with_vm_set(self):
        version = "1.11.9"
        vm_type = helpers._set_vm_set_type("AvailabilitySet", version)
        self.assertEqual(vm_type, "AvailabilitySet")

    def test_no_vm_set(self):
        version = "1.15.0"
        vm_type = helpers._set_vm_set_type("", version)
        self.assertEqual(vm_type, "VirtualMachineScaleSets")

    def test_casing_vmss(self):
        version = "1.15.0"
        vm_type = helpers._set_vm_set_type("virtualmachineScaleSets", version)
        self.assertEqual(vm_type, "VirtualMachineScaleSets")

    def test_casing_as(self):
        version = "1.15.0"
        vm_type = helpers._set_vm_set_type("Availabilityset", version)
        self.assertEqual(vm_type, "AvailabilitySet")
