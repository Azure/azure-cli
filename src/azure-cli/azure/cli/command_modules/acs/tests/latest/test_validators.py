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


class Namespace:
    def __init__(self, api_server_authorized_ip_ranges):
        self.api_server_authorized_ip_ranges = api_server_authorized_ip_ranges


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


class TestLabels(unittest.TestCase):
    def test_invalid_labels_prefix(self):
        invalid_labels = "k8s##.io/label1=value"
        namespace = LabelsNamespace(invalid_labels)
        err = ("Invalid label: k8s##.io/label1=value. Prefix part a DNS-1123 label must consist of lower case "
               "alphanumeric characters or '-', and must start and end with an alphanumeric character")

        with self.assertRaises(CLIError) as cm:
            validators.validate_nodepool_labels(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_invalid_labels_prefix_toolong(self):
        self.maxDiff = None
        invalid_labels = ("k8s12345678901234567890123456789012345678901234567890"
                          "k8s12345678901234567890123456789012345678901234567890"
                          "k8s12345678901234567890123456789012345678901234567890"
                          "k8s12345678901234567890123456789012345678901234567890"
                          "k8s12345678901234567890123456789012345678901234567890"
                          "k8s12345678901234567890123456789012345678901234567890"
                          "k8s12345678901234567890123456789012345678901234567890"
                          "k8s12345678901234567890123456789012345678901234567890"
                          "k8s12345678901234567890123456789012345678901234567890"
                          "k8s12345678901234567890123456789012345678901234567890"
                          "k8s12345678901234567890123456789012345678901234567890/label1=value")

        namespace = LabelsNamespace(invalid_labels)
        err = ("Invalid label: %s. Label prefix can't be empty or more than 253 chars." % invalid_labels)

        with self.assertRaises(CLIError) as cm:
            validators.validate_nodepool_labels(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_invalid_labels_wrong_format(self):
        self.maxDiff = None
        invalid_labels = ("label1value")

        namespace = LabelsNamespace(invalid_labels)
        err = ("Invalid label: %s. Label definition must be of format name=value." % invalid_labels)

        with self.assertRaises(CLIError) as cm:
            validators.validate_nodepool_labels(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_invalid_labels_name_toolong(self):
        self.maxDiff = None
        invalid_labels = ("k8s123456789012345678901234567890123456789012345678901234567890123=value")

        namespace = LabelsNamespace(invalid_labels)
        err = ("Invalid label: %s. Label name can't be empty or more than 63 chars." % invalid_labels)

        with self.assertRaises(CLIError) as cm:
            validators.validate_nodepool_labels(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_invalid_labels_name_invalid(self):
        self.maxDiff = None
        invalid_labels = ("k8s1##@@=value")

        namespace = LabelsNamespace(invalid_labels)
        err = ("Invalid label: %s. A qualified name must consist of alphanumeric characters, '-', '_' "
               "or '.', and must start and end with an alphanumeric character (e.g. 'MyName',  or "
               "'my.name',  or '123-abc') with an optional DNS subdomain prefix and '/' (e.g. "
               "'example.com/MyName')" % invalid_labels)

        with self.assertRaises(CLIError) as cm:
            validators.validate_nodepool_labels(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_invalid_labels_value_toolong(self):
        self.maxDiff = None
        invalid_labels = ("label=k8s123456789012345678901234567890123456789012345678901234567890123")

        namespace = LabelsNamespace(invalid_labels)
        err = ("Invalid label: %s. Label must be more than 63 chars." % invalid_labels)

        with self.assertRaises(CLIError) as cm:
            validators.validate_nodepool_labels(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_invalid_labels_value_invalid(self):
        self.maxDiff = None
        invalid_labels = ("label=k8s1##@@")

        namespace = LabelsNamespace(invalid_labels)
        err = ("Invalid label: %s. A valid label must be an empty string or consist of alphanumeric "
               "characters, '-', '_' or '.', and must start and end with an alphanumeric character" % invalid_labels)

        with self.assertRaises(CLIError) as cm:
            validators.validate_nodepool_labels(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_valid_labels(self):
        namespace = LabelsNamespace("k8s.io/label=value")
        validators.validate_nodepool_labels(namespace)

        namespace = LabelsNamespace(["k8s.io/label=value", "label2=value2"])
        validators.validate_nodepool_labels(namespace)


class LabelsNamespace:
    def __init__(self, labels):
        self.labels = labels
