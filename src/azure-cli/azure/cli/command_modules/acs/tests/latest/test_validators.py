# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from azure.cli.core.util import CLIError
from azure.cli.command_modules.acs import _validators as validators


class TestValidateIPRanges(unittest.TestCase):
    def test_simultaneous_allow_and_disallow_with_spaces(self):
        api_server_authorized_ip_ranges = " 0.0.0.0/32 , 129.1.1.1.1 "
        namespace = Namespace(api_server_authorized_ip_ranges)
        err = ("Setting --api-server-authorized-ip-ranges to 0.0.0.0/32 is not allowed with other IP ranges."
               "Refer to https://aka.ms/aks/whitelist for more details")

        with self.assertRaises(CLIError) as cm:
            validators.validate_ip_ranges(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_simultaneous_enable_and_disable_with_spaces(self):
        # an entry of "", 129.1.1.1.1 from command line is translated into " , 129.1.1.1.1"
        api_server_authorized_ip_ranges = " , 129.1.1.1.1"
        namespace = Namespace(api_server_authorized_ip_ranges)
        err = "--api-server-authorized-ip-ranges cannot be disabled and simultaneously enabled"

        with self.assertRaises(CLIError) as cm:
            validators.validate_ip_ranges(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_disable_authorized_ip_ranges(self):
        api_server_authorized_ip_ranges = ''
        namespace = Namespace(api_server_authorized_ip_ranges)
        validators.validate_ip_ranges(namespace)

    def test_local_ip_address(self):
        api_server_authorized_ip_ranges = "192.168.0.0,192.168.0.0/16"
        namespace = Namespace(api_server_authorized_ip_ranges)
        err = "--api-server-authorized-ip-ranges must be global non-reserved addresses or CIDRs"

        with self.assertRaises(CLIError) as cm:
            validators.validate_ip_ranges(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_invalid_ip(self):
        api_server_authorized_ip_ranges = "193.168.0"
        namespace = Namespace(api_server_authorized_ip_ranges)
        err = "--api-server-authorized-ip-ranges should be a list of IPv4 addresses or CIDRs"

        with self.assertRaises(CLIError) as cm:
            validators.validate_ip_ranges(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_IPv6(self):
        api_server_authorized_ip_ranges = "3ffe:1900:4545:3:200:f8ff:fe21:67cf"
        namespace = Namespace(api_server_authorized_ip_ranges)
        err = "--api-server-authorized-ip-ranges cannot be IPv6 addresses"

        with self.assertRaises(CLIError) as cm:
            validators.validate_ip_ranges(namespace)
        self.assertEqual(str(cm.exception), err)


class TestClusterAutoscalerParamsValidators(unittest.TestCase):
    def test_empty_key_empty_value(self):
        cluster_autoscaler_profile = ["="]
        namespace = Namespace(cluster_autoscaler_profile=cluster_autoscaler_profile)
        err = "Empty key specified for cluster-autoscaler-profile"

        with self.assertRaises(CLIError) as cm:
            validators.validate_cluster_autoscaler_profile(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_non_empty_key_empty_value(self):
        cluster_autoscaler_profile = ["key1="]
        namespace = Namespace(cluster_autoscaler_profile=cluster_autoscaler_profile)

        validators.validate_cluster_autoscaler_profile(namespace)

    def test_two_empty_keys_empty_value(self):
        cluster_autoscaler_profile = ["=", "="]
        namespace = Namespace(cluster_autoscaler_profile=cluster_autoscaler_profile)
        err = "Empty key specified for cluster-autoscaler-profile"

        with self.assertRaises(CLIError) as cm:
            validators.validate_cluster_autoscaler_profile(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_one_empty_key_in_pair_one_non_empty(self):
        cluster_autoscaler_profile = ["scan-interval=20s", "="]
        namespace = Namespace(cluster_autoscaler_profile=cluster_autoscaler_profile)
        err = "Empty key specified for cluster-autoscaler-profile"

        with self.assertRaises(CLIError) as cm:
            validators.validate_cluster_autoscaler_profile(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_invalid_key(self):
        cluster_autoscaler_profile = ["bad-key=val"]
        namespace = Namespace(cluster_autoscaler_profile=cluster_autoscaler_profile)
        err = "Invalid key specified for cluster-autoscaler-profile: bad-key"

        with self.assertRaises(CLIError) as cm:
            validators.validate_cluster_autoscaler_profile(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_valid_parameters(self):
        cluster_autoscaler_profile = ["scan-interval=20s", "scale-down-delay-after-add=15m"]
        namespace = Namespace(cluster_autoscaler_profile=cluster_autoscaler_profile)

        validators.validate_cluster_autoscaler_profile(namespace)


class Namespace:
    def __init__(self, api_server_authorized_ip_ranges=None, cluster_autoscaler_profile=None):
        self.api_server_authorized_ip_ranges = api_server_authorized_ip_ranges
        self.cluster_autoscaler_profile = cluster_autoscaler_profile


class TestVNetSubnetId(unittest.TestCase):
    def test_invalid_vnet_subnet_id(self):
        invalid_vnet_subnet_id = "dummy subnet id"
        namespace = VnetSubnetIdNamespace(invalid_vnet_subnet_id)
        err = ("--vnet-subnet-id is not a valid Azure resource ID.")

        with self.assertRaises(CLIError) as cm:
            validators.validate_vnet_subnet_id(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_valid_vnet_subnet_id(self):
        invalid_vnet_subnet_id = "/subscriptions/testid/resourceGroups/MockedResourceGroup/providers/Microsoft.Network/virtualNetworks/MockedNetworkId/subnets/MockedSubNetId"
        namespace = VnetSubnetIdNamespace(invalid_vnet_subnet_id)
        validators.validate_vnet_subnet_id(namespace)

    def test_none_vnet_subnet_id(self):
        invalid_vnet_subnet_id = None
        namespace = VnetSubnetIdNamespace(invalid_vnet_subnet_id)
        validators.validate_vnet_subnet_id(namespace)

    def test_empty_vnet_subnet_id(self):
        invalid_vnet_subnet_id = ""
        namespace = VnetSubnetIdNamespace(invalid_vnet_subnet_id)
        validators.validate_vnet_subnet_id(namespace)


class VnetSubnetIdNamespace:
    def __init__(self, vnet_subnet_id):
        self.vnet_subnet_id = vnet_subnet_id
