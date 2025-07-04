# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

from azure.cli.command_modules.acs import _validators as validators
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    RequiredArgumentMissingError,
    UnknownError,
)
import azure.cli.command_modules.acs.azurecontainerstorage._consts as acstor_consts
import azure.cli.command_modules.acs.azurecontainerstorage._validators as acstor_validator
from azure.cli.core.util import CLIError


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

class MaxUnavailableNamespace:
    def __init__(self, max_unavailable):
        self.max_unavailable = max_unavailable


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

class TestMaxUnavailable(unittest.TestCase):
    def test_valid_cases(self):
        valid = ["5", "33%", "1", "100%", "0"]
        for v in valid:
            validators.validate_max_unavailable(MaxUnavailableNamespace(v))

    def test_throws_on_string(self):
        with self.assertRaises(CLIError) as cm:
            validators.validate_max_unavailable(MaxUnavailableNamespace("foobar"))
        self.assertTrue("int or percentage" in str(cm.exception), msg=str(cm.exception))

    def test_throws_on_negative(self):
        with self.assertRaises(CLIError) as cm:
            validators.validate_max_unavailable(MaxUnavailableNamespace("-3"))
        self.assertTrue("positive" in str(cm.exception), msg=str(cm.exception))

class MessageOfTheDayNamespace:
    def __init__(self, message_of_the_day, os_type):
        self.os_type = os_type
        self.message_of_the_day = message_of_the_day
        
class TestMessageOfTheday(unittest.TestCase):
    def test_valid_cases(self):
        valid = ["foo", ""]
        for v in valid:
            validators.validate_message_of_the_day(MessageOfTheDayNamespace(v, "Linux"))

    def test_fail_if_os_type_windows(self):
        with self.assertRaises(CLIError) as cm:
            validators.validate_message_of_the_day(
                MessageOfTheDayNamespace("foo", "Windows")
            )
        self.assertTrue(
            "--message-of-the-day can only be set for linux nodepools"
            in str(cm.exception),
            msg=str(cm.exception),
        )

    def test_fail_if_os_type_invalid(self):
        with self.assertRaises(CLIError) as cm:
            validators.validate_message_of_the_day(
                MessageOfTheDayNamespace("foo", "invalid")
            )
        self.assertTrue(
            "--message-of-the-day can only be set for linux nodepools"
            in str(cm.exception),
            msg=str(cm.exception),
        )


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
        err = (
            "--kubernetes-version should be the full version number or major.minor version number, "
            'such as "1.7.12" or "1.7"'
        )

        with self.assertRaises(CLIError) as cm:
            validators.validate_k8s_version(namespace)
        self.assertEqual(str(cm.exception), err)

        kubernetes_version = "1."

        namespace = Namespace(kubernetes_version=kubernetes_version)

        with self.assertRaises(CLIError) as cm:
            validators.validate_k8s_version(namespace)
        self.assertEqual(str(cm.exception), err)


class TestKeyVaultSecretsProviderAddon(unittest.TestCase):
    def test_invalid_keyvault_secret_provider_parameters(self):
        namespace = SimpleNamespace(
            **{
                "disable_secret_rotation": True,
                "enable_secret_rotation": True,
            }
        )
        with self.assertRaises(MutuallyExclusiveArgumentError):
            validators.validate_keyvault_secrets_provider_disable_and_enable_parameters(
                namespace
            )

    def test_valid_keyvault_secret_provider_parameters(self):
        namespace_1 = SimpleNamespace(
            **{
                "disable_secret_rotation": True,
                "enable_secret_rotation": False,
            }
        )
        validators.validate_keyvault_secrets_provider_disable_and_enable_parameters(namespace_1)

        namespace_2 = SimpleNamespace(
            **{
                "disable_secret_rotation": False,
                "enable_secret_rotation": True,
            }
        )
        validators.validate_keyvault_secrets_provider_disable_and_enable_parameters(namespace_2)

        namespace_3 = SimpleNamespace(
            **{
                "disable_secret_rotation": False,
                "enable_secret_rotation": False,
            }
        )
        validators.validate_keyvault_secrets_provider_disable_and_enable_parameters(namespace_3)

class CapacityReservationGroupIDNamespace:
    def __init__(self, crg_id):
        self.crg_id = crg_id

class TestValidateCapacityReservationGroupID(unittest.TestCase):
    def test_invalid_crg_id(self):
        invalid_crg_id = "dummy crg id"
        namespace = CapacityReservationGroupIDNamespace(crg_id=invalid_crg_id)
        err = ("--crg-id is not a valid Azure resource ID.")

        with self.assertRaises(CLIError) as cm:
            validators.validate_crg_id(namespace)
        self.assertEqual(str(cm.exception), err)

class HostGroupIDNamespace:
    def __init__(self, host_group_id):
        self.host_group_id = host_group_id


class TestValidateHostGroupID(unittest.TestCase):
    def test_invalid_host_group_id(self):
        invalid_host_group_id = "dummy group id"
        namespace = HostGroupIDNamespace(host_group_id=invalid_host_group_id)
        err = ("--host-group-id is not a valid Azure resource ID.")

        with self.assertRaises(CLIError) as cm:
            validators.validate_host_group_id(namespace)
        self.assertEqual(str(cm.exception), err)


class AzureKeyVaultKmsKeyIdNamespace:

    def __init__(self, azure_keyvault_kms_key_id):
        self.azure_keyvault_kms_key_id = azure_keyvault_kms_key_id


class TestValidateAzureKeyVaultKmsKeyId(unittest.TestCase):
    def test_invalid_azure_keyvault_kms_key_id_without_https(self):
        invalid_azure_keyvault_kms_key_id = "dummy key id"
        namespace = AzureKeyVaultKmsKeyIdNamespace(azure_keyvault_kms_key_id=invalid_azure_keyvault_kms_key_id)
        err = '--azure-keyvault-kms-key-id is not a valid Key Vault key ID. ' \
              'See https://learn.microsoft.com/en-us/azure/key-vault/general/about-keys-secrets-certificates#vault-name-and-object-name'

        with self.assertRaises(CLIError) as cm:
            validators.validate_azure_keyvault_kms_key_id(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_invalid_azure_keyvault_kms_key_id_without_key_version(self):
        invalid_azure_keyvault_kms_key_id = "https://fakekeyvault.vault.azure.net/keys/fakekeyname"
        namespace = AzureKeyVaultKmsKeyIdNamespace(azure_keyvault_kms_key_id=invalid_azure_keyvault_kms_key_id)
        err = '--azure-keyvault-kms-key-id is not a valid Key Vault key ID. ' \
              'See https://learn.microsoft.com/en-us/azure/key-vault/general/about-keys-secrets-certificates#vault-name-and-object-name'

        with self.assertRaises(CLIError) as cm:
            validators.validate_azure_keyvault_kms_key_id(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_invalid_azure_keyvault_kms_key_id_with_wrong_object_type(self):
        invalid_azure_keyvault_kms_key_id = "https://fakekeyvault.vault.azure.net/secrets/fakesecretname/fakesecretversion"
        namespace = AzureKeyVaultKmsKeyIdNamespace(azure_keyvault_kms_key_id=invalid_azure_keyvault_kms_key_id)
        err = '--azure-keyvault-kms-key-id is not a valid Key Vault key ID. ' \
              'See https://learn.microsoft.com/en-us/azure/key-vault/general/about-keys-secrets-certificates#vault-name-and-object-name'

        with self.assertRaises(CLIError) as cm:
            validators.validate_azure_keyvault_kms_key_id(namespace)
        self.assertEqual(str(cm.exception), err)

class ImageCleanerNamespace:
    def __init__(
        self,
        enable_image_cleaner=False,
        disable_image_cleaner=False,
        image_cleaner_interval_hours=None,
    ):
        self.enable_image_cleaner = enable_image_cleaner
        self.disable_image_cleaner = disable_image_cleaner
        self.image_cleaner_interval_hours = image_cleaner_interval_hours

class TestValidateImageCleanerEnableDiasble(unittest.TestCase):
    def test_invalid_image_cleaner_enable_disable_not_existing_together(self):
        namespace = ImageCleanerNamespace(
            enable_image_cleaner=True,
            disable_image_cleaner=True,
        )
        err = 'Cannot specify --enable-image-cleaner and --disable-image-cleaner at the same time.'

        with self.assertRaises(CLIError) as cm:
            validators.validate_image_cleaner_enable_disable_mutually_exclusive(namespace)
        self.assertEqual(str(cm.exception), err)

class ForceUpgradeNamespace:
    def __init__(
        self,
        enable_force_upgrade=False,
        disable_force_upgrade=False,
    ):
        self.enable_force_upgrade = enable_force_upgrade
        self.disable_force_upgrade = disable_force_upgrade

class TestValidateForceUpgradeEnableDiasble(unittest.TestCase):
    def test_invalid_force_upgrade_enable_disable_not_existing_together(self):
        namespace = ForceUpgradeNamespace(
            enable_force_upgrade=True,
            disable_force_upgrade=True,
        )
        err = 'Providing both --disable-force-upgrade and --enable-force-upgrade flags is invalid'

        with self.assertRaises(CLIError) as cm:
            validators.validate_force_upgrade_disable_and_enable_parameters(namespace)
        self.assertEqual(str(cm.exception), err)

class AzureKeyVaultKmsKeyVaultResourceIdNamespace:

    def __init__(self, azure_keyvault_kms_key_vault_resource_id):
        self.azure_keyvault_kms_key_vault_resource_id = azure_keyvault_kms_key_vault_resource_id


class TestValidateAzureKeyVaultKmsKeyVaultResourceId(unittest.TestCase):
    def test_invalid_azure_keyvault_kms_key_vault_resource_id(self):
        invalid_azure_keyvault_kms_key_vault_resource_id = "invalid"
        namespace = AzureKeyVaultKmsKeyVaultResourceIdNamespace(azure_keyvault_kms_key_vault_resource_id=invalid_azure_keyvault_kms_key_vault_resource_id)
        err = '--azure-keyvault-kms-key-vault-resource-id is not a valid Azure resource ID.'

        with self.assertRaises(InvalidArgumentValueError) as cm:
            validators.validate_azure_keyvault_kms_key_vault_resource_id(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_valid_azure_keyvault_kms_key_vault_resource_id(self):
        valid_azure_keyvault_kms_key_vault_resource_id = "/subscriptions/8ecadfc9-d1a3-4ea4-b844-0d9f87e4d7c8/resourceGroups/foo/providers/Microsoft.KeyVault/vaults/foo"
        namespace = AzureKeyVaultKmsKeyVaultResourceIdNamespace(azure_keyvault_kms_key_vault_resource_id=valid_azure_keyvault_kms_key_vault_resource_id)

        validators.validate_azure_keyvault_kms_key_vault_resource_id(namespace)


class TestValidateNodepoolName(unittest.TestCase):
    def test_invalid_nodepool_name_too_long(self):
        namespace = SimpleNamespace(
            **{
                "nodepool_name": "tooLongNodepoolName",
            }
        )
        with self.assertRaises(InvalidArgumentValueError):
            validators.validate_nodepool_name(
                namespace
            )

    def test_invalid_agent_pool_name_too_long(self):
        namespace = SimpleNamespace(
            **{
                "agent_pool_name": "tooLongNodepoolName",
            }
        )
        with self.assertRaises(InvalidArgumentValueError):
            validators.validate_agent_pool_name(
                namespace
            )

    def test_invalid_nodepool_name_not_alnum(self):
        namespace = SimpleNamespace(
            **{
                "nodepool_name": "invalid-np*",
            }
        )
        with self.assertRaises(InvalidArgumentValueError):
            validators.validate_nodepool_name(
                namespace
            )

    def test_invalid_agent_pool_name_not_alnum(self):
        namespace = SimpleNamespace(
            **{
                "agent_pool_name": "invalid-np*",
            }
        )
        with self.assertRaises(InvalidArgumentValueError):
            validators.validate_agent_pool_name(
                namespace
            )

    def test_valid_nodepool_name(self):
        namespace = SimpleNamespace(
            **{
                "nodepool_name": "np100",
            }
        )
        validators.validate_nodepool_name(
            namespace
        )

    def test_valid_agent_pool_name(self):
        namespace = SimpleNamespace(
            **{
                "agent_pool_name": "np100",
            }
        )
        validators.validate_agent_pool_name(
            namespace
        )


class GatewayPrefixSizeSpace:
    def __init__(self, gateway_prefix_size=None, mode=None):
        self.gateway_prefix_size = gateway_prefix_size
        self.mode = mode


class TestValidateGatewayPrefixSize(unittest.TestCase):
    def test_none_gateway_prefix_size(self):
        namespace = GatewayPrefixSizeSpace()
        validators.validate_gateway_prefix_size(namespace)

    def test_invalid_gateway_prefix_size_1(self):
        namespace = GatewayPrefixSizeSpace(gateway_prefix_size=27, mode="Gateway")
        err = '--gateway-prefix-size must be in the range [28, 31]'
        with self.assertRaises(CLIError) as cm:
            validators.validate_gateway_prefix_size(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_invalid_gateway_prefix_size_2(self):
        namespace = GatewayPrefixSizeSpace(gateway_prefix_size=32, mode="Gateway")
        err = '--gateway-prefix-size must be in the range [28, 31]'
        with self.assertRaises(CLIError) as cm:
            validators.validate_gateway_prefix_size(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_invalid_mode(self):
        namespace = GatewayPrefixSizeSpace(gateway_prefix_size=31, mode="System")
        err = '--gateway-prefix-size can only be set for Gateway-mode nodepools'
        with self.assertRaises(CLIError) as cm:
            validators.validate_gateway_prefix_size(namespace)
        self.assertEqual(str(cm.exception), err)

    def test_valid_gateway_prefix_size(self):
        namespace = GatewayPrefixSizeSpace(gateway_prefix_size=30, mode="Gateway")
        validators.validate_gateway_prefix_size(namespace)


class TestValidateRegistryName(unittest.TestCase):
    def test_append_suffix(self):
        from azure.cli.core.cloud import HARD_CODED_CLOUD_LIST, CloudSuffixNotSetException
        for hard_coded_cloud in HARD_CODED_CLOUD_LIST:
            namespace = SimpleNamespace(
                **{
                    "acr": "myacr",
                }
            )
            try:
                acr_suffix = hard_coded_cloud.suffixes.acr_login_server_endpoint
            except CloudSuffixNotSetException:
                acr_suffix = ""
            cmd = Mock(cli_ctx=Mock(cloud=hard_coded_cloud))
            validators.validate_registry_name(cmd, namespace)
            self.assertEqual(namespace.acr, "myacr" + acr_suffix)

class TestValidateAllowedHostPorts(unittest.TestCase):
    def test_invalid_allowed_host_ports(self):
        namespace = SimpleNamespace(
            **{
                "allowed_host_ports": ["80"],
            }
        )
        with self.assertRaises(InvalidArgumentValueError):
            validators.validate_allowed_host_ports(
                namespace
            )

    def test_valid_allowed_host_ports(self):
        namespace = SimpleNamespace(
            **{
                "allowed_host_ports": ["80/tcp", "443/tcp", "8080-8090/tcp", "53/udp"],
            }
        )
        validators.validate_allowed_host_ports(
            namespace
        )


class TestValidateApplicationSecurityGroups(unittest.TestCase):
    def test_invalid_application_security_groups(self):
        namespace = SimpleNamespace(
            **{
                "asg_ids": "invalid",
                "allowed_host_ports": ["80/tcp", "443/tcp", "8080-8090/tcp", "53/udp"],
            }
        )
        with self.assertRaises(InvalidArgumentValueError):
            validators.validate_application_security_groups(
                namespace
            )

    def test_application_security_groups_without_allowed_host_ports(self):
        asg_ids = [
            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg1/providers/Microsoft.Network/applicationSecurityGroups/asg1",
        ]
        namespace = SimpleNamespace(
            **{
                "asg_ids": asg_ids,
                "allowed_host_ports": [],
            }
        )
        with self.assertRaises(ArgumentUsageError):
            validators.validate_application_security_groups(
                namespace
            )

    def test_nodepool_application_security_groups_without_allowed_host_ports(self):
        asg_ids = [
            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg1/providers/Microsoft.Network/applicationSecurityGroups/asg1",
        ]
        namespace = SimpleNamespace(
            **{
                "nodepool_asg_ids": asg_ids,
                "nodepool_allowed_host_ports": [],
            }
        )
        with self.assertRaises(ArgumentUsageError):
            validators.validate_application_security_groups(
                namespace
            )

    def test_empty_application_security_groups(self):
        namespace = SimpleNamespace(
            **{
                "asg_ids": "",
                "allowed_host_ports": [],
            }
        )
        validators.validate_application_security_groups(
            namespace
        )

    def test_empty_nodepool_application_security_groups(self):
        namespace = SimpleNamespace(
            **{
                "nodepool_asg_ids": "",
                "nodepool_allowed_host_ports": [],
            }
        )
        validators.validate_application_security_groups(
            namespace
        )

    def test_multiple_application_security_groups(self):
        asg_ids = [
            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg1/providers/Microsoft.Network/applicationSecurityGroups/asg1",
            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg2/providers/Microsoft.Network/applicationSecurityGroups/asg2",
        ]
        namespace = SimpleNamespace(
            **{
                "asg_ids": asg_ids,
                "allowed_host_ports": ["80/tcp", "443/tcp", "8080-8090/tcp", "53/udp"],
            }
        )
        validators.validate_application_security_groups(
            namespace
        )

    def test_multiple_nodepool_application_security_groups(self):
        asg_ids = [
            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg1/providers/Microsoft.Network/applicationSecurityGroups/asg1",
            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg2/providers/Microsoft.Network/applicationSecurityGroups/asg2",
        ]
        namespace = SimpleNamespace(
            **{
                "nodepool_asg_ids": asg_ids,
                "nodepool_allowed_host_ports": ["80/tcp", "443/tcp", "8080-8090/tcp", "53/udp"],
            }
        )
        validators.validate_application_security_groups(
            namespace
        )


class TestValidateDisableAzureContainerStorage(unittest.TestCase):
    def test_disable_when_extension_not_installed(self):
        is_extension_installed = False
        err = (
            "Invalid usage of --disable-azure-container-storage. "
            "Azure Container Storage is not enabled in the cluster."
        )
        with self.assertRaises(InvalidArgumentValueError) as cm:
            acstor_validator.validate_disable_azure_container_storage_params(
                None, None, None, None, None, None, is_extension_installed, False, False, False, False, None, None
            )
        self.assertEqual(str(cm.exception), err)

    def test_disable_flag_with_storage_pool_name(self):
        storage_pool_name = "pool-name"
        err = (
            "Conflicting flags. Cannot define --storage-pool-name value "
            "when --disable-azure-container-storage is set."
        )
        with self.assertRaises(MutuallyExclusiveArgumentError) as cm:
            acstor_validator.validate_disable_azure_container_storage_params(
                None, storage_pool_name, None, None, None, None, True, False, False, False, False, None, None
            )
        self.assertEqual(str(cm.exception), err)

    def test_disable_flag_with_storage_pool_sku(self):
        storage_pool_sku = acstor_consts.CONST_STORAGE_POOL_SKU_PREMIUM_LRS
        err = (
            "Conflicting flags. Cannot define --storage-pool-sku value "
            "when --disable-azure-container-storage is set."
        )
        with self.assertRaises(MutuallyExclusiveArgumentError) as cm:
            acstor_validator.validate_disable_azure_container_storage_params(
                None, None, storage_pool_sku, None, None, None, True, False, False, False, False, None, None
            )
        self.assertEqual(str(cm.exception), err)

    def test_disable_flag_with_storage_pool_size(self):
        storage_pool_size = "5Gi"
        err = (
            "Conflicting flags. Cannot define --storage-pool-size value "
            "when --disable-azure-container-storage is set."
        )
        with self.assertRaises(MutuallyExclusiveArgumentError) as cm:
            acstor_validator.validate_disable_azure_container_storage_params(
                None, None, None, None, storage_pool_size, None, True, False, False, False, False, None, None
            )
        self.assertEqual(str(cm.exception), err)

    def test_disable_flag_with_ephemeral_disk_volume_type(self):
        storage_pool_size = "5Gi"
        ephemeral_disk_volume_type = acstor_consts.CONST_DISK_TYPE_PV_WITH_ANNOTATION
        err = (
            "Conflicting flags. Cannot define --ephemeral-disk-volume-type value "
            "when --disable-azure-container-storage is set."
        )
        with self.assertRaises(MutuallyExclusiveArgumentError) as cm:
            acstor_validator.validate_disable_azure_container_storage_params(
                None, None, None, None, None, None, True, False, False, False, False, ephemeral_disk_volume_type, None
            )
        self.assertEqual(str(cm.exception), err)

    def test_disable_flag_with_ephemeral_disk_nvme_perf_tier(self):
        storage_pool_size = "5Gi"
        ephemeral_disk_volume_type = acstor_consts.CONST_DISK_TYPE_PV_WITH_ANNOTATION
        perf_tier = acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_PREMIUM
        err = (
            "Conflicting flags. Cannot define --ephemeral-disk-nvme-perf-tier value "
            "when --disable-azure-container-storage is set."
        )
        with self.assertRaises(MutuallyExclusiveArgumentError) as cm:
            acstor_validator.validate_disable_azure_container_storage_params(
                None, None, None, None, None, None, True, False, False, False, False, None, perf_tier
            )
        self.assertEqual(str(cm.exception), err)

    def test_disable_flag_with_storage_pool_option_not_ephemeralDisk(self):
        storage_pool_option = acstor_consts.CONST_STORAGE_POOL_OPTION_NVME
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        err = (
            "Cannot define --storage-pool-option value when "
            "--disable-azure-container-storage is not set to ephemeralDisk."
        )
        with self.assertRaises(ArgumentUsageError) as cm:
            acstor_validator.validate_disable_azure_container_storage_params(
                storage_pool_type, None, None, storage_pool_option, None, None, True, False, False, False, False, None, None
            )
        self.assertEqual(str(cm.exception), err)

    def test_disable_flag_with_storage_pool_option_not_set_both_ephemeralDisk_enabled(self):
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        err = (
            "Value of --storage-pool-option must be defined since ephemeralDisk of both "
            "the types: NVMe and Temp are enabled in the cluster."
        )
        with self.assertRaises(RequiredArgumentMissingError) as cm:
            acstor_validator.validate_disable_azure_container_storage_params(
                storage_pool_type, None, None, None, None, None, True, False, False, True, True, None, None
            )
        self.assertEqual(str(cm.exception), err)

    def test_disable_flag_with_nodepool_list(self):
        nodepool_list = "test,test1"
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        err = (
            "Conflicting flags. Cannot define --azure-container-storage-nodepools value "
            "when --disable-azure-container-storage is set."
        )
        with self.assertRaises(MutuallyExclusiveArgumentError) as cm:
            acstor_validator.validate_disable_azure_container_storage_params(
                storage_pool_type, None, None, None, None, nodepool_list, True, False, False, False, False, None, None
            )
        self.assertEqual(str(cm.exception), err)

    def test_disable_type_when_not_enabled(self):
        pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        is_azureDisk_enabled = False
        err = (
            "Invalid --disable-azure-container-storage value. "
            "Azure Container Storage is not enabled for storage pool "
            "type {0} in the cluster.".format(pool_type)
        )
        with self.assertRaises(ArgumentUsageError) as cm:
            acstor_validator.validate_disable_azure_container_storage_params(
                pool_type, None, None, None, None, None, True, is_azureDisk_enabled, False, False, False, None, None
            )
        self.assertEqual(str(cm.exception), err)

    def test_disable_only_storage_pool_installed(self):
        pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        err = (
            "Since azureDisk is the only storage pool type enabled for Azure Container Storage, "
            "disabling the storage pool type will lead to disabling Azure Container Storage from the cluster. "
            "To disable Azure Container Storage, set --disable-azure-container-storage to all."
        )
        with self.assertRaises(ArgumentUsageError) as cm:
            acstor_validator.validate_disable_azure_container_storage_params(
                pool_type, None, None, None, None, None, True, True, False, False, False, None, None
            )
        self.assertEqual(str(cm.exception), err)

    def test_disable_only_storagepool_type_enabled(self):
        pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        is_azureDisk_enabled = True
        err = (
            "Since azureDisk is the only storage pool type enabled for Azure Container Storage, "
            "disabling the storage pool type will lead to disabling Azure Container Storage from the cluster. "
            "To disable Azure Container Storage, set --disable-azure-container-storage to all."
        )
        with self.assertRaises(ArgumentUsageError) as cm:
            acstor_validator.validate_disable_azure_container_storage_params(
                pool_type, None, None, None, None, None, True, is_azureDisk_enabled, False, False, False, None, None
            )
        self.assertEqual(str(cm.exception), err)

    def test_valid_disable(self):
        pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_ELASTIC_SAN
        acstor_validator.validate_disable_azure_container_storage_params(
            pool_type, None, None, None, None, None, True, False, True, True, False, None, None
        )


class TestValidateEnableAzureContainerStorage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def side_effect_fn(sku_name):
            if sku_name == "standard_l8s_v3":
                return 8, True
            elif sku_name == "standard_d2s_v2":
                return 2, False
            elif sku_name == "standard_d2pds_v6":
                return 2, True
            elif sku_name == "standard_ds1_v2":
                return 1, False
            elif sku_name == "standard_m8-2ms":
                return 2, False
            elif sku_name == "standard_b2s":
                return 2, False

            return None, None

        cls.patcher = patch('azure.cli.command_modules.acs.azurecontainerstorage._validators.get_vm_sku_details')
        cls.mock_fn = cls.patcher.start()
        cls.mock_fn.side_effect = side_effect_fn

    @classmethod
    def tearDownClass(cls):
        # Stop the patcher
        cls.patcher.stop()

    def test_enable_with_invalid_storage_pool_name(self):
        storage_pool_name = "my_test_pool"
        err = (
            "Invalid --storage-pool-name value. "
            "Accepted values are lowercase alphanumeric characters, "
            "'-' or '.', and must start and end with an alphanumeric character."
        )
        with self.assertRaises(InvalidArgumentValueError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                None, storage_pool_name, None, None, None, None, None, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_sku_and_ephemeral_disk_pool(self):
        storage_pool_name = "valid-name"
        storage_pool_sku = acstor_consts.CONST_STORAGE_POOL_SKU_PREMIUM_LRS
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        err = "Cannot set --storage-pool-sku when --enable-azure-container-storage is ephemeralDisk."
        with self.assertRaises(ArgumentUsageError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, storage_pool_sku, None, None, None, None, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_sku_and_elastic_san_pool(self):
        storage_pool_name = "valid-name"
        storage_pool_sku = acstor_consts.CONST_STORAGE_POOL_SKU_PREMIUMV2_LRS
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_ELASTIC_SAN
        supported_skus = (
            acstor_consts.CONST_STORAGE_POOL_SKU_PREMIUM_LRS
            + ", "
            + acstor_consts.CONST_STORAGE_POOL_SKU_PREMIUM_ZRS
        )
        err = (
            "Invalid --storage-pool-sku value. "
            "Supported value for --storage-pool-sku are {0} "
            "when --enable-azure-container-storage is set to elasticSan.".format(
                supported_skus
            )
        )
        with self.assertRaises(ArgumentUsageError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, storage_pool_sku, None, None, None, None, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_premiumv2_sku_and_azure_disk(self):
        storage_pool_name = "valid-name"
        storage_pool_sku = acstor_consts.CONST_STORAGE_POOL_SKU_PREMIUMV2_LRS
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        nodepool_list = "pool1"
        agentpools = {"pool1": {"vm_size": "Standard_L8s_v3", "count": 3, "zoned": False}}
        err = (
            "Cannot set --storage-pool-sku as {0} "
            "as none of the node pools are zoned. "
            "Please add a zoned node pool and try again.".format(
                storage_pool_sku
            )
        )
        with self.assertRaises(ArgumentUsageError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, storage_pool_sku, None, None, nodepool_list, agentpools, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_insufficient_cores_1(self):
        storage_pool_name = "valid-name"
        storage_pool_sku = acstor_consts.CONST_STORAGE_POOL_SKU_PREMIUM_LRS
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        nodepool_list = "pool1"
        agentpools = {"pool1": {"vm_size": "Standard_D2s_v2", "count": 3, "zoned": False}}
        err = (
            "Cannot operate Azure Container Storage on a node pool consisting of "
            "nodes with cores less than 4. Node pool: pool1 with node size: Standard_D2s_v2 "
            "which is assigned for Azure Container Storage has nodes with 2 cores."
        )
        with self.assertRaises(InvalidArgumentValueError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, storage_pool_sku, None, None, nodepool_list, agentpools, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_insufficient_cores_2(self):
        storage_pool_name = "valid-name"
        storage_pool_sku = acstor_consts.CONST_STORAGE_POOL_SKU_PREMIUM_LRS
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        nodepool_list = "pool1"
        agentpools = {"pool1": {"vm_size": "Standard_D2pds_v6", "count": 3, "zoned": False}}
        err = (
            "Cannot operate Azure Container Storage on a node pool consisting of "
            "nodes with cores less than 4. Node pool: pool1 with node size: Standard_D2pds_v6 "
            "which is assigned for Azure Container Storage has nodes with 2 cores."
        )
        with self.assertRaises(InvalidArgumentValueError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, storage_pool_sku, None, None, nodepool_list, agentpools, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_insufficient_cores_3(self):
        storage_pool_name = "valid-name"
        storage_pool_sku = acstor_consts.CONST_STORAGE_POOL_SKU_PREMIUM_LRS
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        nodepool_list = "pool1"
        agentpools = {"pool1": {"vm_size": "Standard_Ds1_v2", "count": 3, "zoned": False}}
        err = (
            "Cannot operate Azure Container Storage on a node pool consisting of "
            "nodes with cores less than 4. Node pool: pool1 with node size: Standard_Ds1_v2 "
            "which is assigned for Azure Container Storage has nodes with 1 cores."
        )
        with self.assertRaises(InvalidArgumentValueError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, storage_pool_sku, None, None, nodepool_list, agentpools, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_insufficient_cores_4(self):
        storage_pool_name = "valid-name"
        storage_pool_sku = acstor_consts.CONST_STORAGE_POOL_SKU_PREMIUM_LRS
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        nodepool_list = "pool1"
        agentpools = {"pool1": {"vm_size": "Standard_M8-2ms", "count": 3, "zoned": False}}
        err = (
            "Cannot operate Azure Container Storage on a node pool consisting of "
            "nodes with cores less than 4. Node pool: pool1 with node size: Standard_M8-2ms "
            "which is assigned for Azure Container Storage has nodes with 2 cores."
        )
        with self.assertRaises(InvalidArgumentValueError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, storage_pool_sku, None, None, nodepool_list, agentpools, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_insufficient_cores_5(self):
        storage_pool_name = "valid-name"
        storage_pool_sku = acstor_consts.CONST_STORAGE_POOL_SKU_PREMIUM_LRS
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        nodepool_list = "pool1"
        agentpools = {"pool1": {"vm_size": "Standard_B2s", "count": 3, "zoned": False}}
        err = (
            "Cannot operate Azure Container Storage on a node pool consisting of "
            "nodes with cores less than 4. Node pool: pool1 with node size: Standard_B2s "
            "which is assigned for Azure Container Storage has nodes with 2 cores."
        )
        with self.assertRaises(InvalidArgumentValueError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, storage_pool_sku, None, None, nodepool_list, agentpools, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_option_and_non_ephemeral_disk_pool(self):
        storage_pool_name = "valid-name"
        storage_pool_option = acstor_consts.CONST_STORAGE_POOL_OPTION_NVME
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        err = "Cannot set --storage-pool-option when --enable-azure-container-storage is not ephemeralDisk."
        with self.assertRaises(ArgumentUsageError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, None, storage_pool_option, None, None, None, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_ephemeral_disk_volume_type_and_non_ephemeral_disk_pool(self):
        storage_pool_name = "valid-name"
        ephemeral_disk_volume_type = acstor_consts.CONST_DISK_TYPE_PV_WITH_ANNOTATION
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        err = "Cannot set --ephemeral-disk-volume-type when --enable-azure-container-storage is not ephemeralDisk."
        with self.assertRaises(ArgumentUsageError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, None, None, None, None, None, False, False, False, False, False, ephemeral_disk_volume_type, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_ephemeral_disk_nvme_perf_tier_and_non_ephemeral_disk_pool(self):
        storage_pool_name = "valid-name"
        perf_tier = acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_PREMIUM
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        err = (
            "Cannot set --ephemeral-disk-nvme-perf-tier when --enable-azure-container-storage is not ephemeralDisk."
        )
        with self.assertRaises(ArgumentUsageError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, None, None, None, None, None, False, False, False, False, False, None, perf_tier, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_ephemeral_disk_nvme_perf_tier_and_ephemeral_temp_disk_pool(self):
        storage_pool_name = "valid-name"
        perf_tier = acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_PREMIUM
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        storage_pool_option = acstor_consts.CONST_STORAGE_POOL_OPTION_SSD
        err = (
            "Cannot set --ephemeral-disk-nvme-perf-tier along with --enable-azure-container-storage "
            "when storage pool type: ephemeralDisk option: NVMe is not enabled for Azure Container Storage. "
            "Enable the option using --storage-pool-option."
        )
        with self.assertRaises(ArgumentUsageError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, None, storage_pool_option, None, None, None, False, False, False, False, False, None, perf_tier, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_same_ephemeral_disk_nvme_perf_tier_already_set(self):
        perf_tier = acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_PREMIUM
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        err = (
                "Azure Container Storage is already configured with --ephemeral-disk-nvme-perf-tier "
                f"value set to {perf_tier}."
        )
        with self.assertRaises(InvalidArgumentValueError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, None, None, None, None, None, None, True, False, False, False, True, None, perf_tier, acstor_consts.CONST_DISK_TYPE_PV_WITH_ANNOTATION, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_PREMIUM
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_same_ephemeral_disk_volume_type_already_set(self):
        disk_vol_type = acstor_consts.CONST_DISK_TYPE_PV_WITH_ANNOTATION
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        err = (
                "Azure Container Storage is already configured with --ephemeral-disk-volume-type "
                f"value set to {disk_vol_type}."
        )
        with self.assertRaises(InvalidArgumentValueError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, None, None, None, None, None, None, True, False, False, False, True, disk_vol_type, None, acstor_consts.CONST_DISK_TYPE_PV_WITH_ANNOTATION, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_PREMIUM
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_same_ephemeral_disk_nvme_perf_tier_and_ephemeral_temp_disk_pool_already_set(self):
        perf_tier = acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
        disk_vol_type = acstor_consts.CONST_DISK_TYPE_PV_WITH_ANNOTATION
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        err = (
                "Azure Container Storage is already configured with --ephemeral-disk-volume-type "
                f"value set to {disk_vol_type} and --ephemeral-disk-nvme-perf-tier "
                f"value set to {perf_tier}."
        )
        with self.assertRaises(InvalidArgumentValueError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, None, None, None, None, None, None, True, False, False, False, True, disk_vol_type, perf_tier, acstor_consts.CONST_DISK_TYPE_PV_WITH_ANNOTATION, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_option_all_and_ephemeral_disk_pool(self):
        storage_pool_name = "valid-name"
        storage_pool_option = acstor_consts.CONST_ACSTOR_ALL
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        err = "Cannot set --storage-pool-option value as all when --enable-azure-container-storage is set."
        with self.assertRaises(InvalidArgumentValueError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, None, storage_pool_option, None, None, None, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_invalid_storage_pool_size(self):
        storage_pool_name = "valid-name"
        storage_pool_size = "5"
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        err = "Value for --storage-pool-size should be defined with size followed by Gi or Ti e.g. 512Gi or 2Ti."
        with self.assertRaises(ArgumentUsageError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, None, None, storage_pool_size, None, None, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_enable_with_invalid_size_for_esan_storage_pool(self):
        storage_pool_name = "valid-name"
        storage_pool_size = "512Gi"
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_ELASTIC_SAN
        err = "Value for --storage-pool-size must be at least 1Ti when --enable-azure-container-storage is elasticSan."
        with self.assertRaises(ArgumentUsageError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, None, None, storage_pool_size, None, None, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_invalid_comma_separated_nodepool_list(self):
        nodepool_list = "pool1, 1pool"
        storage_pool_name = "valid-name"
        storage_pool_size = "5Ti"
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        err = (
            "Invalid --azure-container-storage-nodepools value. "
            "Accepted value is a comma separated string of valid node pool "
            "names without any spaces.\nA valid node pool name may only contain lowercase "
            "alphanumeric characters and must begin with a lowercase letter."
        )
        with self.assertRaises(InvalidArgumentValueError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, None, None, storage_pool_size, nodepool_list, None, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_missing_nodepool_from_cluster_nodepool_list_single(self):
        storage_pool_name = "valid-name"
        storage_pool_size = "5Ti"
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        storage_pool_option = acstor_consts.CONST_STORAGE_POOL_OPTION_NVME
        nodepool_list = "pool1"
        agentpools = {"nodepool1": {"vm_size": "Standard_L8s_v3"}}
        err = (
            "Node pool: pool1 not found. Please provide a comma separated "
            "string of existing node pool names in --azure-container-storage-nodepools."
            "\nNode pool available in the cluster: nodepool1."
            "\nAborting installation of Azure Container Storage."
        )
        with self.assertRaises(InvalidArgumentValueError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, None, storage_pool_option, storage_pool_size, nodepool_list, agentpools, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_missing_nodepool_from_cluster_nodepool_list_multiple(self):
        storage_pool_name = "valid-name"
        storage_pool_size = "5Ti"
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        storage_pool_option = acstor_consts.CONST_STORAGE_POOL_OPTION_SSD
        nodepool_list = "pool1,pool2"
        agentpools = {"nodepool1": {}, "nodepool2":{}}
        err = (
            "Node pool: pool1 not found. Please provide a comma separated "
            "string of existing node pool names in --azure-container-storage-nodepools."
            "\nNode pools available in the cluster: nodepool1, nodepool2."
            "\nAborting installation of Azure Container Storage."
        )
        with self.assertRaises(InvalidArgumentValueError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, None, storage_pool_option, storage_pool_size, nodepool_list, agentpools, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_system_nodepool_with_taint(self):
        storage_pool_name = "valid-name"
        storage_pool_size = "5Ti"
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        storage_pool_option = acstor_consts.CONST_STORAGE_POOL_OPTION_SSD
        nodepool_list = "nodepool1"
        agentpools = {"nodepool1": {"mode": "System", "node_taints": ["CriticalAddonsOnly=true:NoSchedule"]}, "nodepool2": {"count": 1}}
        err = (
            'Unable to install Azure Container Storage on system nodepool: nodepool1 '
            'since it has a taint CriticalAddonsOnly=true:NoSchedule. Remove the taint from the node pool '
            'and retry the Azure Container Storage operation.'
        )
        with self.assertRaises(InvalidArgumentValueError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, None, storage_pool_option, storage_pool_size, nodepool_list, agentpools, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_nodepool_from_cluster_nodepool_list_with_insufficient_count(self):
        storage_pool_name = "valid-name"
        storage_pool_size = "5Ti"
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        storage_pool_option = acstor_consts.CONST_STORAGE_POOL_OPTION_SSD
        nodepool_list = "nodepool1,nodepool2"
        agentpools = {"nodepool1": {"count": 1}, "nodepool2": {"count": 1}}
        err = (
            "Insufficient nodes present. Azure Container Storage requires atleast 3 nodes to be enabled."
        )
        with self.assertRaises(UnknownError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, None, storage_pool_option, storage_pool_size, nodepool_list, agentpools, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_valid_enable_for_azure_disk_pool(self):
        storage_pool_name = "valid-name"
        storage_pool_size = "5Ti"
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        storage_pool_sku = acstor_consts.CONST_STORAGE_POOL_SKU_PREMIUM_LRS
        nodepool_list = "nodepool1,nodepool2"
        agentpools = {"nodepool1": {"mode": "User", "count": 2}, "nodepool2": {"mode": "System", "count": 1}}
        acstor_validator.validate_enable_azure_container_storage_params(
            storage_pool_type, storage_pool_name, storage_pool_sku, None, storage_pool_size, nodepool_list, agentpools, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
        )

    def test_valid_enable_for_ephemeral_disk_pool(self):
        storage_pool_name = "valid-name"
        storage_pool_size = "5Ti"
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        storage_pool_option = acstor_consts.CONST_STORAGE_POOL_OPTION_NVME
        nodepool_list = "nodepool1"
        agentpools = {"nodepool1": {"vm_size": "Standard_L8s_v3", "mode": "System", "count": 5}, "nodepool2": {"vm_size": "Standard_L8s_v3"}}
        acstor_validator.validate_enable_azure_container_storage_params(
            storage_pool_type, storage_pool_name, None, storage_pool_option, storage_pool_size, nodepool_list, agentpools, False, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
        )

    def test_valid_enable_for_ephemeral_disk_pool_with_ephemeral_disk_volume_type(self):
        storage_pool_name = "valid-name"
        storage_pool_size = "5Ti"
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        storage_pool_option = acstor_consts.CONST_STORAGE_POOL_OPTION_NVME
        nodepool_list = "nodepool1"
        ephemeral_disk_volume_type = acstor_consts.CONST_DISK_TYPE_PV_WITH_ANNOTATION
        agentpools = {"nodepool1": {"vm_size": "Standard_L8s_v3", "mode": "System", "count": 3}, "nodepool2": {"vm_size": "Standard_L8s_v3"}}
        acstor_validator.validate_enable_azure_container_storage_params(
            storage_pool_type, storage_pool_name, None, storage_pool_option, storage_pool_size, nodepool_list, agentpools, False, False, False, False, False, ephemeral_disk_volume_type, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
        )

    def test_valid_enable_for_ephemeral_disk_pool_with_ephemeral_disk_volume_type_already_installed(self):
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        ephemeral_disk_volume_type = acstor_consts.CONST_DISK_TYPE_PV_WITH_ANNOTATION
        agentpools = {"nodepool1": {"node_labels": {"acstor.azure.com/io-engine": "acstor"}, "count": 3}, "nodepool2": {}}
        acstor_validator.validate_enable_azure_container_storage_params(
            storage_pool_type, None, None, None, None, None, agentpools, True, False, False, True, False, ephemeral_disk_volume_type, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
        )

    def test_valid_enable_for_ephemeral_disk_pool_with_ephemeral_disk_nvme_perf_tier(self):
        storage_pool_name = "valid-name"
        storage_pool_size = "5Ti"
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        storage_pool_option = acstor_consts.CONST_STORAGE_POOL_OPTION_NVME
        nodepool_list = "nodepool1"
        perf_tier = acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_PREMIUM
        agentpools = {"nodepool1": {"vm_size": "Standard_L8s_v3", "count": 4}, "nodepool2": {"vm_size": "Standard_L8s_v3"}}
        acstor_validator.validate_enable_azure_container_storage_params(
            storage_pool_type, storage_pool_name, None, storage_pool_option, storage_pool_size, nodepool_list, agentpools, False, False, False, False, False, None, perf_tier, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
        )

    def test_valid_enable_for_ephemeral_disk_pool_with_azure_container_storage_per_tier_nvme_already_installed(self):
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK
        perf_tier = acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_PREMIUM
        agentpools = {"nodepool1": {"node_labels": {"acstor.azure.com/io-engine": "acstor"}, "count": 3}, "nodepool2": {}}
        acstor_validator.validate_enable_azure_container_storage_params(
            storage_pool_type, None, None, None, None, None, agentpools, True, False, False, False, True, None, perf_tier, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
        )

    def test_extension_installed_nodepool_list_defined(self):
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        nodepool_list = "nodepool1,nodepool2"
        err = (
            "Cannot set --azure-container-storage-nodepools while using "
            "--enable-azure-container-storage to enable a type of storage pool "
            "in a cluster where Azure Container Storage is already installed. "
            "Use 'az aks nodepool' to label the node pool instead."
        )
        with self.assertRaises(ArgumentUsageError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, None, None, None, None, nodepool_list, None, True, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_extension_installed_storagepool_type_installed(self):
        storage_pool_name = "valid-name"
        storage_pool_size = "5Ti"
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        storage_pool_sku = acstor_consts.CONST_STORAGE_POOL_SKU_PREMIUM_LRS
        agentpools = {"nodepool1": {"node_labels": {"acstor.azure.com/io-engine": "acstor"}, "count": 3}, "nodepool2" :{}}
        err = (
            "Invalid --enable-azure-container-storage value. "
            "Azure Container Storage is already enabled for storage pool type "
            "{0} in the cluster.".format(storage_pool_type)
        )
        with self.assertRaises(ArgumentUsageError) as cm:
            acstor_validator.validate_enable_azure_container_storage_params(
                storage_pool_type, storage_pool_name, storage_pool_sku, None, storage_pool_size, None, agentpools, True, True, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
            )
        self.assertEqual(str(cm.exception), err)

    def test_valid_cluster_update(self):
        storage_pool_name = "valid-name"
        storage_pool_size = "5Ti"
        storage_pool_type = acstor_consts.CONST_STORAGE_POOL_TYPE_AZURE_DISK
        storage_pool_sku = acstor_consts.CONST_STORAGE_POOL_SKU_PREMIUM_LRS
        agentpools = {"nodepool1": {"node_labels": {"acstor.azure.com/io-engine": "acstor"}, "mode": "User", "count": 3}, "nodepool2": {}}
        acstor_validator.validate_enable_azure_container_storage_params(
            storage_pool_type, storage_pool_name, storage_pool_sku, None, storage_pool_size, None, agentpools, True, False, False, False, False, None, None, acstor_consts.CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY, acstor_consts.CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
        )


class DisableWindowsOutboundNatNamespace:
    def __init__(self, os_type, disable_windows_outbound_nat):
        self.os_type = os_type
        self.disable_windows_outbound_nat = disable_windows_outbound_nat


class TestDisableWindowsOutboundNAT(unittest.TestCase):
    def test_pass_if_os_type_windows(self):
        validators.validate_disable_windows_outbound_nat(
            DisableWindowsOutboundNatNamespace("Windows", True)
        )

    def test_fail_if_os_type_linux(self):
        with self.assertRaises(CLIError) as cm:
            validators.validate_disable_windows_outbound_nat(
                DisableWindowsOutboundNatNamespace("Linux", True)
            )
        self.assertTrue(
            "--disable-windows-outbound-nat can only be set for Windows nodepools"
            in str(cm.exception),
            msg=str(cm.exception),
        )

    def test_fail_if_os_type_invalid(self):
        with self.assertRaises(CLIError) as cm:
            validators.validate_disable_windows_outbound_nat(
                DisableWindowsOutboundNatNamespace("invalid", True)
            )
        self.assertTrue(
            "--disable-windows-outbound-nat can only be set for Windows nodepools"
            in str(cm.exception),
            msg=str(cm.exception),
        )

class CustomCATrustCertificatesNamespace:
    def __init__(self, os_type, custom_ca_trust_certificates):
        self.os_type = os_type
        self.custom_ca_trust_certificates = custom_ca_trust_certificates
class TestCustomCATrustCertificates(unittest.TestCase):
    def test_valid_cases(self):
        valid = ["foo", ""]
        for v in valid:
            validators.validate_custom_ca_trust_certificates(CustomCATrustCertificatesNamespace("Linux", v))

    def test_fail_if_os_type_windows(self):
        with self.assertRaises(CLIError) as cm:
            validators.validate_custom_ca_trust_certificates(CustomCATrustCertificatesNamespace("Windows", "foo"))
        self.assertTrue('--custom-ca-trust-certificates can only be set for linux nodepools' in str(cm.exception), msg=str(cm.exception))

    def test_fail_if_os_type_invalid(self):
        with self.assertRaises(CLIError) as cm:
            validators.validate_custom_ca_trust_certificates(CustomCATrustCertificatesNamespace("invalid", "foo"))
        self.assertTrue('--custom-ca-trust-certificates can only be set for linux nodepools' in str(cm.exception), msg=str(cm.exception))


if __name__ == "__main__":
    unittest.main()
