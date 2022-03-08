# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from knack import CLI

from azure.cli.core._config import GLOBAL_CONFIG_DIR, ENV_VAR_PREFIX
from azure.cli.core.cloud import get_active_cloud
from azure.cli.core.profiles import get_sdk, ResourceType, supported_api_version

from azure.cli.command_modules.acs import _helpers as helpers

class MockCLI(CLI):
    def __init__(self):
        super(MockCLI, self).__init__(cli_name='mock_cli', config_dir=GLOBAL_CONFIG_DIR,
                                      config_env_var_prefix=ENV_VAR_PREFIX, commands_loader_cls=MockLoader)
        self.cloud = get_active_cloud(self)


class MockLoader(object):
    def __init__(self, ctx):
        self.ctx = ctx

    def get_models(self, *attr_args, **_):
        from azure.cli.core.profiles import get_sdk
        return get_sdk(self.ctx, ResourceType.MGMT_CONTAINERSERVICE, 'ManagedClusterAPIServerAccessProfile',
                       mod='models', operation_group='managed_clusters')


class MockCmd(object):
    def __init__(self, ctx, arguments={}):
        self.cli_ctx = ctx
        self.loader = MockLoader(self.cli_ctx)
        self.arguments = arguments

    def get_models(self, *attr_args, **kwargs):
        return get_sdk(self.cli_ctx, ResourceType.MGMT_CONTAINERSERVICE, 'ManagedClusterAPIServerAccessProfile',
                       mod='models', operation_group='managed_clusters')


class TestPopulateApiServerAccessProfile(unittest.TestCase):
    def setUp(self):
        self.cli = MockCLI()

    def test_single_cidr_with_spaces(self):
        api_server_authorized_ip_ranges = "0.0.0.0/32 "
        profile = helpers._populate_api_server_access_profile(MockCmd(self.cli), api_server_authorized_ip_ranges, enable_private_cluster=False)
        self.assertListEqual(profile.authorized_ip_ranges, ["0.0.0.0/32"])

    def test_multi_cidr_with_spaces(self):
        api_server_authorized_ip_ranges = " 0.0.0.0/32 , 129.1.1.1/32"
        profile = helpers._populate_api_server_access_profile(MockCmd(self.cli), api_server_authorized_ip_ranges, enable_private_cluster=False)
        self.assertListEqual(profile.authorized_ip_ranges, ["0.0.0.0/32", "129.1.1.1/32"])

    def test_private_cluster(self):
        profile = helpers._populate_api_server_access_profile(MockCmd(self.cli), None, enable_private_cluster=True)
        self.assertListEqual(profile.authorized_ip_ranges, [])
        self.assertEqual(profile.enable_private_cluster, True)


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
