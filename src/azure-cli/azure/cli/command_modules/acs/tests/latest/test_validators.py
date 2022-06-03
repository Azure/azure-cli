# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

from azure.cli.command_modules.acs import _validators as validators
from azure.cli.core._config import ENV_VAR_PREFIX, GLOBAL_CONFIG_DIR
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.cloud import get_active_cloud
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.cli.core.util import CLIError
from knack import CLI

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
        return get_sdk(self.ctx, ResourceType.MGMT_CONTAINERSERVICE, 'ManagedClusterPropertiesAutoScalerProfile',
                       mod='models', operation_group='managed_clusters')


class MockCmd(object):
    def __init__(self, ctx, arguments={}):
        self.cli_ctx = ctx
        self.loader = MockLoader(self.cli_ctx)
        self.arguments = arguments

    def get_models(self, *attr_args, **kwargs):
        return get_sdk(self.cli_ctx, ResourceType.MGMT_CONTAINERSERVICE, 'ManagedClusterPropertiesAutoScalerProfile',
                       mod='models', operation_group='managed_clusters')


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
    def __init__(self, api_server_authorized_ip_ranges=None, cluster_autoscaler_profile=None, kubernetes_version=None):
        self.api_server_authorized_ip_ranges = api_server_authorized_ip_ranges
        self.cluster_autoscaler_profile = cluster_autoscaler_profile
        self.kubernetes_version = kubernetes_version


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

class TestPodSubnetId(unittest.TestCase):
    def test_invalid_pod_subnet_id(self):
        invalid_pod_subnet_id = "dummy subnet id"
        namespace = PodSubnetIdNamespace(invalid_pod_subnet_id)
        err = ("--pod-subnet-id is not a valid Azure resource ID.")

        with self.assertRaises(CLIError) as cm:
            validators.validate_pod_subnet_id(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_valid_pod_subnet_id(self):
        invalid_pod_subnet_id = "/subscriptions/testid/resourceGroups/MockedResourceGroup/providers/Microsoft.Network/virtualNetworks/MockedNetworkId/subnets/MockedSubNetId"
        namespace = PodSubnetIdNamespace(invalid_pod_subnet_id)
        validators.validate_pod_subnet_id(namespace)

    def test_none_pod_subnet_id(self):
        invalid_pod_subnet_id = None
        namespace = PodSubnetIdNamespace(invalid_pod_subnet_id)
        validators.validate_pod_subnet_id(namespace)

    def test_empty_pod_subnet_id(self):
        invalid_pod_subnet_id = ""
        namespace = PodSubnetIdNamespace(invalid_pod_subnet_id)
        validators.validate_pod_subnet_id(namespace)


class PodSubnetIdNamespace:
    def __init__(self, pod_subnet_id):
        self.pod_subnet_id = pod_subnet_id


class MaxSurgeNamespace:
    def __init__(self, max_surge):
        self.max_surge = max_surge


class TestMaxSurge(unittest.TestCase):
    def test_valid_cases(self):
        valid = ["5", "33%", "1", "100%"]
        for v in valid:
            validators.validate_max_surge(MaxSurgeNamespace(v))

    def test_throws_on_string(self):
        with self.assertRaises(CLIError) as cm:
            validators.validate_max_surge(MaxSurgeNamespace("foobar"))
        self.assertTrue('int or percentage' in str(cm.exception), msg=str(cm.exception))

    def test_throws_on_negative(self):
        with self.assertRaises(CLIError) as cm:
            validators.validate_max_surge(MaxSurgeNamespace("-3"))
        self.assertTrue('positive' in str(cm.exception), msg=str(cm.exception))


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
        err = ("Invalid label: %s. Label must not be more than 63 chars." % invalid_labels)

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


class AssignIdentityNamespace:
    def __init__(self, assign_identity):
        self.assign_identity = assign_identity


class TestAssignIdentity(unittest.TestCase):
    def test_invalid_identity_id(self):
        invalid_identity_id = "dummy identity id"
        namespace = AssignIdentityNamespace(invalid_identity_id)
        err = ("--assign-identity is not a valid Azure resource ID.")

        with self.assertRaises(CLIError) as cm:
            validators.validate_assign_identity(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_valid_identity_id(self):
        valid_identity_id = "/subscriptions/testid/resourceGroups/MockedResourceGroup/providers/Microsoft.ManagedIdentity/userAssignedIdentities/mockIdentityID"
        namespace = AssignIdentityNamespace(valid_identity_id)
        validators.validate_assign_identity(namespace)

    def test_none_identity_id(self):
        none_identity_id = None
        namespace = AssignIdentityNamespace(none_identity_id)
        validators.validate_assign_identity(namespace)

    def test_empty_identity_id(self):
        empty_identity_id = ""
        namespace = AssignIdentityNamespace(empty_identity_id)
        validators.validate_assign_identity(namespace)


class TestExtractCommaSeparatedString(unittest.TestCase):
    def test_extract_comma_separated_string(self):
        s1 = None
        t1 = validators.extract_comma_separated_string(s1, keep_none=True, default_value="")
        g1 = None
        self.assertEqual(t1, g1)

        s2 = None
        t2 = validators.extract_comma_separated_string(s2, keep_none=False, default_value="")
        g2 = ""
        self.assertEqual(t2, g2)

        s3 = ""
        t3 = validators.extract_comma_separated_string(s3, keep_none=True, default_value={})
        g3 = {}
        self.assertEqual(t3, g3)

        s4 = "abc, xyz, 123"
        t4 = validators.extract_comma_separated_string(s4)
        g4 = ["abc", " xyz", " 123"]
        self.assertEqual(t4, g4)

        s5 = "abc, xyz, 123"
        t5 = validators.extract_comma_separated_string(s5, enable_strip=True)
        g5 = ["abc", "xyz", "123"]
        self.assertEqual(t5, g5)

        s6 = "abc = def, xyz = 123"
        t6 = validators.extract_comma_separated_string(s6, extract_kv=True)
        g6 = {"abc ": " def", " xyz ": " 123"}
        self.assertEqual(t6, g6)

        s7 = "abc = def, xyz = 123"
        t7 = validators.extract_comma_separated_string(s7, enable_strip=True, extract_kv=True)
        g7 = {"abc": "def", "xyz": "123"}
        self.assertEqual(t7, g7)

        s8 = "abc = def, xyz = "
        t8 = validators.extract_comma_separated_string(s8, extract_kv=True, allow_empty_value=True)
        g8 = {"abc ": " def", " xyz ": " "}
        self.assertEqual(t8, g8)

        s9 = "abc = def, xyz = "
        t9 = validators.extract_comma_separated_string(s9, enable_strip=True, extract_kv=True, allow_empty_value=True)
        g9 = {"abc": "def", "xyz": ""}
        self.assertEqual(t9, g9)

        s10 = "abc = def, xyz = "
        with self.assertRaises(InvalidArgumentValueError):
            validators.extract_comma_separated_string(s10, extract_kv=True)

        s11 = "abc def, xyz 123"
        with self.assertRaises(InvalidArgumentValueError):
            validators.extract_comma_separated_string(s11, extract_kv=True)

        s12 = "abc=def=xyz,123=456"
        with self.assertRaises(InvalidArgumentValueError):
            validators.extract_comma_separated_string(s12, extract_kv=True)

        s13 = "WindowsContainerRuntime=containerd,AKSHTTPCustomFeatures=Microsoft.ContainerService/CustomNodeConfigPreview"
        t13 = validators.extract_comma_separated_string(s13, enable_strip=True, extract_kv=True, default_value={}, allow_appending_values_to_same_key=True)
        g13 = {"WindowsContainerRuntime": "containerd", "AKSHTTPCustomFeatures": "Microsoft.ContainerService/CustomNodeConfigPreview"}
        self.assertEqual(t13, g13)

        s14 = "="
        t14 = validators.extract_comma_separated_string(s14, extract_kv=True, allow_empty_value=True)
        g14 = {"": ""}
        self.assertEqual(t14, g14)

        s15 = "WindowsContainerRuntime=containerd,AKSHTTPCustomFeatures=Microsoft.ContainerService/AKSTestFeaturePreview,AKSHTTPCustomFeatures=Microsoft.ContainerService/AKSExampleFeaturePreview"
        t15 = validators.extract_comma_separated_string(s15, enable_strip=True, extract_kv=True, default_value={},)
        g15 = {"WindowsContainerRuntime": "containerd", "AKSHTTPCustomFeatures": "Microsoft.ContainerService/AKSExampleFeaturePreview"}
        self.assertEqual(t15, g15)

        s16 = "WindowsContainerRuntime=containerd,AKSHTTPCustomFeatures=Microsoft.ContainerService/AKSTestFeaturePreview,AKSHTTPCustomFeatures=Microsoft.ContainerService/AKSExampleFeaturePreview"
        t16 = validators.extract_comma_separated_string(s16, enable_strip=True, extract_kv=True, default_value={}, allow_appending_values_to_same_key=True)
        g16 = {"WindowsContainerRuntime": "containerd", "AKSHTTPCustomFeatures": "Microsoft.ContainerService/AKSTestFeaturePreview,Microsoft.ContainerService/AKSExampleFeaturePreview"}
        self.assertEqual(t16, g16)


class CredentialFormatNamespace:
    def __init__(self, credential_format):
        self.credential_format = credential_format


class TestCredentialFormat(unittest.TestCase):
    def test_invalid_format(self):
        credential_format = "foobar"
        namespace = CredentialFormatNamespace(credential_format)
        err = ("--format can only be azure or exec.")

        with self.assertRaises(CLIError) as cm:
            validators.validate_credential_format(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_valid_format(self):
        credential_format = "exec"
        namespace = CredentialFormatNamespace(credential_format)

        validators.validate_credential_format(namespace)

class TestValidateKubernetesVersion(unittest.TestCase):

     def test_valid_full_kubernetes_version(self):
         kubernetes_version = "1.11.8"
         namespace = Namespace(kubernetes_version=kubernetes_version)

         validators.validate_k8s_version(namespace)

     def test_valid_alias_minor_version(self):
         kubernetes_version = "1.11"
         namespace = Namespace(kubernetes_version=kubernetes_version)

         validators.validate_k8s_version(namespace)

     def test_valid_empty_kubernetes_version(self):
         kubernetes_version = ""
         namespace = Namespace(kubernetes_version=kubernetes_version)

         validators.validate_k8s_version(namespace)

     def test_invalid_kubernetes_version(self):
         kubernetes_version = "1.2.3.4"

         namespace = Namespace(kubernetes_version=kubernetes_version)
         err = ("--kubernetes-version should be the full version number or major.minor version number, "
                "such as \"1.7.12\" or \"1.7\"")

         with self.assertRaises(CLIError) as cm:
             validators.validate_k8s_version(namespace)
         self.assertEqual(str(cm.exception), err)

         kubernetes_version = "1."

         namespace = Namespace(kubernetes_version=kubernetes_version)

         with self.assertRaises(CLIError) as cm:
             validators.validate_k8s_version(namespace)
         self.assertEqual(str(cm.exception), err)


if __name__ == "__main__":
    unittest.main()
