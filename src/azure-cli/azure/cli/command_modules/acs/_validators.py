# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import unicode_literals

import os
import re
from ipaddress import ip_network
from math import isclose, isnan

from azure.cli.core import keys
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    RequiredArgumentMissingError,
)
from azure.cli.core.commands.validators import validate_tag
from azure.cli.core.util import CLIError
from knack.log import get_logger

logger = get_logger(__name__)


def validate_ssh_key(namespace):
    if hasattr(namespace, 'no_ssh_key') and namespace.no_ssh_key:
        return
    string_or_file = (namespace.ssh_key_value or
                      os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa.pub'))
    content = string_or_file
    if os.path.exists(string_or_file):
        logger.info('Use existing SSH public key file: %s', string_or_file)
        with open(string_or_file, 'r') as f:
            content = f.read()
    elif not keys.is_valid_ssh_rsa_public_key(content):
        if namespace.generate_ssh_keys:
            # figure out appropriate file names:
            # 'base_name'(with private keys), and 'base_name.pub'(with public keys)
            public_key_filepath = string_or_file
            if public_key_filepath[-4:].lower() == '.pub':
                private_key_filepath = public_key_filepath[:-4]
            else:
                private_key_filepath = public_key_filepath + '.private'
            content = keys.generate_ssh_keys(private_key_filepath, public_key_filepath)
            logger.warning("SSH key files '%s' and '%s' have been generated under ~/.ssh to "
                           "allow SSH access to the VM. If using machines without "
                           "permanent storage like Azure Cloud Shell without an attached "
                           "file share, back up your keys to a safe location",
                           private_key_filepath, public_key_filepath)
        else:
            raise CLIError('An RSA key file or key value must be supplied to SSH Key Value. '
                           'You can use --generate-ssh-keys to let CLI generate one for you')
    namespace.ssh_key_value = content


def validate_create_parameters(namespace):
    if not namespace.name:
        raise CLIError('--name has no value')
    if namespace.dns_name_prefix is not None and not namespace.dns_name_prefix:
        raise CLIError('--dns-prefix has no value')


def validate_ip_ranges(namespace):
    if not namespace.api_server_authorized_ip_ranges:
        return

    restrict_traffic_to_agentnodes = "0.0.0.0/32"
    allow_all_traffic = ""
    ip_ranges = [ip.strip() for ip in namespace.api_server_authorized_ip_ranges.split(",")]

    if restrict_traffic_to_agentnodes in ip_ranges and len(ip_ranges) > 1:
        raise CLIError(("Setting --api-server-authorized-ip-ranges to 0.0.0.0/32 is not allowed with other IP ranges."
                        "Refer to https://aka.ms/aks/whitelist for more details"))

    if allow_all_traffic in ip_ranges and len(ip_ranges) > 1:
        raise CLIError("--api-server-authorized-ip-ranges cannot be disabled and simultaneously enabled")

    for ip in ip_ranges:
        if ip in [restrict_traffic_to_agentnodes, allow_all_traffic]:
            continue
        try:
            ip = ip_network(ip)
            if not ip.is_global:
                raise CLIError("--api-server-authorized-ip-ranges must be global non-reserved addresses or CIDRs")
            if ip.version == 6:
                raise CLIError("--api-server-authorized-ip-ranges cannot be IPv6 addresses")
        except ValueError:
            raise CLIError("--api-server-authorized-ip-ranges should be a list of IPv4 addresses or CIDRs")


def validate_k8s_version(namespace):
    """Validates a string as a possible Kubernetes version. An empty string is also valid, which tells the server
    to use its default version."""
    if namespace.kubernetes_version:
        k8s_release_regex = re.compile(r'^[v|V]?(\d+\.\d+(?:\.\d+)?)$')
        found = k8s_release_regex.findall(namespace.kubernetes_version)
        if found:
            namespace.kubernetes_version = found[0]
        else:
            raise CLIError('--kubernetes-version should be the full version number or major.minor version number, '
                           'such as "1.7.12" or "1.7"')


def _validate_nodepool_name(nodepool_name):
    """Validates a nodepool name to be at most 12 characters, alphanumeric only."""
    if nodepool_name != "":
        if len(nodepool_name) > 12:
            raise InvalidArgumentValueError('--nodepool-name can contain at most 12 characters')
        if not nodepool_name.isalnum():
            raise InvalidArgumentValueError('--nodepool-name should contain only alphanumeric characters')


def validate_nodepool_name(namespace):
    """Validates a nodepool name to be at most 12 characters, alphanumeric only."""
    _validate_nodepool_name(namespace.nodepool_name)


def validate_agent_pool_name(namespace):
    """Validates a nodepool name to be at most 12 characters, alphanumeric only."""
    _validate_nodepool_name(namespace.agent_pool_name)


def validate_kubectl_version(namespace):
    """Validates a string as a possible Kubernetes version."""
    k8s_release_regex = re.compile(r'^[v|V]?(\d+\.\d+\.\d+.*|latest)$')
    found = k8s_release_regex.findall(namespace.client_version)
    if found:
        namespace.client_version = found[0]
    else:
        raise CLIError('--client-version should be the full version number '
                       '(such as "1.11.8" or "1.12.6") or "latest"')


def validate_kubelogin_version(namespace):
    """Validates a string as a possible kubelogin version."""
    kubelogin_regex = re.compile(r'^[v|V]?(\d+\.\d+\.\d+.*|latest)$')
    found = kubelogin_regex.findall(namespace.kubelogin_version)
    if found:
        namespace.kubelogin_version = found[0]
    else:
        raise CLIError('--kubelogin-version should be the full version number '
                       '(such as "0.0.4") or "latest"')


def validate_linux_host_name(namespace):
    """Validates a string as a legal host name component.

    This validation will also occur server-side in the ARM API, but that may take
    a minute or two before the user sees it. So it's more user-friendly to validate
    in the CLI pre-flight.
    """
    # https://stackoverflow.com/questions/106179/regular-expression-to-match-dns-hostname-or-ip-address
    rfc1123_regex = re.compile(r'^[a-zA-Z0-9]$|^[a-zA-Z0-9][-_a-zA-Z0-9]{0,61}[a-zA-Z0-9]$')  # pylint:disable=line-too-long
    found = rfc1123_regex.findall(namespace.name)
    if not found:
        raise InvalidArgumentValueError('--name cannot exceed 63 characters and can only contain '
                                        'letters, numbers, underscores (_) or dashes (-).')


def validate_snapshot_name(namespace):
    """Validates a nodepool snapshot name to be alphanumeric and dashes."""
    rfc1123_regex = re.compile(r'^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])(\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]))*$')  # pylint:disable=line-too-long
    found = rfc1123_regex.findall(namespace.snapshot_name)
    if not found:
        raise InvalidArgumentValueError('--name cannot exceed 63 characters and can only contain '
                                        'letters, numbers, or dashes (-).')


def validate_vm_set_type(namespace):
    """Validates the vm set type string."""
    if namespace.vm_set_type is not None:
        if namespace.vm_set_type == '':
            return
        if namespace.vm_set_type.lower() != "availabilityset" and \
                namespace.vm_set_type.lower() != "virtualmachinescalesets":
            raise CLIError("--vm-set-type can only be VirtualMachineScaleSets or AvailabilitySet")


def validate_load_balancer_sku(namespace):
    """Validates the load balancer sku string."""
    if namespace.load_balancer_sku is not None:
        if namespace.load_balancer_sku == '':
            return
        if namespace.load_balancer_sku.lower() != "basic" and namespace.load_balancer_sku.lower() != "standard":
            raise CLIError("--load-balancer-sku can only be standard or basic")


def validate_load_balancer_outbound_ips(namespace):
    """validate load balancer profile outbound IP ids"""
    if namespace.load_balancer_outbound_ips is not None:
        ip_id_list = [x.strip() for x in namespace.load_balancer_outbound_ips.split(',')]
        if not all(ip_id_list):
            raise CLIError("--load-balancer-outbound-ips cannot contain whitespace")


def validate_load_balancer_outbound_ip_prefixes(namespace):
    """validate load balancer profile outbound IP prefix ids"""
    if namespace.load_balancer_outbound_ip_prefixes is not None:
        ip_prefix_id_list = [x.strip() for x in namespace.load_balancer_outbound_ip_prefixes.split(',')]
        if not all(ip_prefix_id_list):
            raise CLIError("--load-balancer-outbound-ip-prefixes cannot contain whitespace")


def validate_load_balancer_outbound_ports(namespace):
    """validate load balancer profile outbound allocated ports"""
    if namespace.load_balancer_outbound_ports is not None:
        if namespace.load_balancer_outbound_ports % 8 != 0:
            raise CLIError("--load-balancer-allocated-ports must be a multiple of 8")
        if namespace.load_balancer_outbound_ports < 0 or namespace.load_balancer_outbound_ports > 64000:
            raise CLIError("--load-balancer-allocated-ports must be in the range [0,64000]")


def validate_load_balancer_idle_timeout(namespace):
    """validate load balancer profile idle timeout"""
    if namespace.load_balancer_idle_timeout is not None:
        if namespace.load_balancer_idle_timeout < 4 or namespace.load_balancer_idle_timeout > 100:
            raise CLIError("--load-balancer-idle-timeout must be in the range [4,100]")


def validate_network_policy(namespace):
    """validate network policy to be in lowercase"""
    if namespace.network_policy is not None and namespace.network_policy.islower() is False:
        raise InvalidArgumentValueError("--network-policy should be provided in lowercase")


def validate_nat_gateway_managed_outbound_ip_count(namespace):
    """validate NAT gateway profile managed outbound IP count"""
    if namespace.nat_gateway_managed_outbound_ip_count is not None:
        if namespace.nat_gateway_managed_outbound_ip_count < 1 or namespace.nat_gateway_managed_outbound_ip_count > 16:
            raise InvalidArgumentValueError("--nat-gateway-managed-outbound-ip-count must be in the range [1,16]")


def validate_nat_gateway_idle_timeout(namespace):
    """validate NAT gateway profile idle timeout"""
    if namespace.nat_gateway_idle_timeout is not None:
        if namespace.nat_gateway_idle_timeout < 4 or namespace.nat_gateway_idle_timeout > 120:
            raise InvalidArgumentValueError("--nat-gateway-idle-timeout must be in the range [4,120]")


def validate_nodes_count(namespace):
    """Validates that min_count and max_count is set between 0-1000"""
    if namespace.min_count is not None:
        if namespace.min_count < 0 or namespace.min_count > 1000:
            raise CLIError('--min-count must be in the range [0,1000]')
    if namespace.max_count is not None:
        if namespace.max_count < 0 or namespace.max_count > 1000:
            raise CLIError('--max-count must be in the range [0,1000]')


def validate_taints(namespace):
    """Validates that provided taint is a valid format"""

    regex = re.compile(r"^[a-zA-Z\d][\w\-\.\/]{0,252}=[a-zA-Z\d][\w\-\.]{0,62}:(NoSchedule|PreferNoSchedule|NoExecute)$")  # pylint: disable=line-too-long

    if namespace.node_taints is not None and namespace.node_taints != '':
        for taint in namespace.node_taints.split(','):
            if taint == "":
                continue
            found = regex.findall(taint)
            if not found:
                raise CLIError('Invalid node taint: %s' % taint)


def validate_priority(namespace):
    """Validates the node pool priority string."""
    if namespace.priority is not None:
        if namespace.priority == '':
            return
        if namespace.priority != "Spot" and \
                namespace.priority != "Regular":
            raise CLIError("--priority can only be Spot or Regular")


def validate_eviction_policy(namespace):
    """Validates the node pool priority string."""
    if namespace.eviction_policy is not None:
        if namespace.eviction_policy == '':
            return
        if namespace.eviction_policy != "Delete" and \
                namespace.eviction_policy != "Deallocate":
            raise CLIError("--eviction-policy can only be Delete or Deallocate")


def validate_spot_max_price(namespace):
    """Validates the spot node pool max price."""
    if not isnan(namespace.spot_max_price):
        if namespace.priority != "Spot":
            raise CLIError("--spot_max_price can only be set when --priority is Spot")
        if len(str(namespace.spot_max_price).split(".")) > 1 and len(str(namespace.spot_max_price).split(".")[1]) > 5:
            raise CLIError("--spot_max_price can only include up to 5 decimal places")
        if namespace.spot_max_price <= 0 and not isclose(namespace.spot_max_price, -1.0, rel_tol=1e-06):
            raise CLIError(
                "--spot_max_price can only be any decimal value greater than zero, or -1 which indicates "
                "default price to be up-to on-demand")


def validate_acr(namespace):
    if namespace.attach_acr and namespace.detach_acr:
        raise CLIError('Cannot specify "--attach-acr" and "--detach-acr" at the same time.')


def validate_nodepool_tags(ns):
    """ Extracts multiple space-separated tags in key[=value] format """
    if isinstance(ns.nodepool_tags, list):
        tags_dict = {}
        for item in ns.nodepool_tags:
            tags_dict.update(validate_tag(item))
        ns.nodepool_tags = tags_dict


def validate_vnet_subnet_id(namespace):
    _validate_subnet_id(namespace.vnet_subnet_id, "--vnet-subnet-id")


def validate_pod_subnet_id(namespace):
    _validate_subnet_id(namespace.pod_subnet_id, "--pod-subnet-id")


def _validate_subnet_id(subnet_id, name):
    if subnet_id is None or subnet_id == '':
        return
    from msrestazure.tools import is_valid_resource_id
    if not is_valid_resource_id(subnet_id):
        raise InvalidArgumentValueError(name + " is not a valid Azure resource ID.")


def validate_ppg(namespace):
    if namespace.ppg is not None:
        if namespace.ppg == '':
            return
        from msrestazure.tools import is_valid_resource_id
        if not is_valid_resource_id(namespace.ppg):
            raise CLIError("--ppg is not a valid Azure resource ID.")


def validate_nodepool_labels(namespace):
    """Validates that provided node labels is a valid format"""

    if hasattr(namespace, 'nodepool_labels'):
        labels = namespace.nodepool_labels
    else:
        labels = namespace.labels

    if labels is None:
        return

    if isinstance(labels, list):
        labels_dict = {}
        for item in labels:
            labels_dict.update(validate_label(item))
        after_validation_labels = labels_dict
    else:
        after_validation_labels = validate_label(labels)

    if hasattr(namespace, 'nodepool_labels'):
        namespace.nodepool_labels = after_validation_labels
    else:
        namespace.labels = after_validation_labels


def validate_label(label):
    """Validates that provided label is a valid format"""
    prefix_regex = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$")
    name_regex = re.compile(r"^([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9]$")
    value_regex = re.compile(r"^(([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9])?$")

    if label == "":
        return {}
    kv = label.split('=')
    if len(kv) != 2:
        raise CLIError("Invalid label: %s. Label definition must be of format name=value." % label)
    name_parts = kv[0].split('/')
    if len(name_parts) == 1:
        name = name_parts[0]
    elif len(name_parts) == 2:
        prefix = name_parts[0]
        if not prefix or len(prefix) > 253:
            raise CLIError("Invalid label: %s. Label prefix can't be empty or more than 253 chars." % label)
        if not prefix_regex.match(prefix):
            raise CLIError("Invalid label: %s. Prefix part a DNS-1123 label must consist of lower case alphanumeric "
                           "characters or '-', and must start and end with an alphanumeric character" % label)
        name = name_parts[1]
    else:
        raise CLIError("Invalid label: %s. A qualified name must consist of alphanumeric characters, '-', '_' "
                       "or '.', and must start and end with an alphanumeric character (e.g. 'MyName',  or "
                       "'my.name',  or '123-abc') with an optional DNS subdomain prefix and '/' "
                       "(e.g. 'example.com/MyName')" % label)

    # validate label name
    if not name or len(name) > 63:
        raise CLIError("Invalid label: %s. Label name can't be empty or more than 63 chars." % label)
    if not name_regex.match(name):
        raise CLIError("Invalid label: %s. A qualified name must consist of alphanumeric characters, '-', '_' "
                       "or '.', and must start and end with an alphanumeric character (e.g. 'MyName',  or "
                       "'my.name',  or '123-abc') with an optional DNS subdomain prefix and '/' (e.g. "
                       "'example.com/MyName')" % label)

    # validate label value
    if len(kv[1]) > 63:
        raise CLIError("Invalid label: %s. Label must not be more than 63 chars." % label)
    if not value_regex.match(kv[1]):
        raise CLIError("Invalid label: %s. A valid label must be an empty string or consist of alphanumeric "
                       "characters, '-', '_' or '.', and must start and end with an alphanumeric character" % label)

    return {kv[0]: kv[1]}


def validate_max_surge(namespace):
    """validates parameters like max surge are postive integers or percents. less strict than RP"""
    if namespace.max_surge is None:
        return
    int_or_percent = namespace.max_surge
    if int_or_percent.endswith('%'):
        int_or_percent = int_or_percent.rstrip('%')

    try:
        if int(int_or_percent) < 0:
            raise CLIError("--max-surge must be positive")
    except ValueError:
        raise CLIError("--max-surge should be an int or percentage")


def validate_assign_identity(namespace):
    if namespace.assign_identity is not None:
        if namespace.assign_identity == '':
            return
        from msrestazure.tools import is_valid_resource_id
        if not is_valid_resource_id(namespace.assign_identity):
            raise InvalidArgumentValueError("--assign-identity is not a valid Azure resource ID.")


def validate_assign_kubelet_identity(namespace):
    if namespace.assign_kubelet_identity is not None:
        if namespace.assign_kubelet_identity == '':
            return
        from msrestazure.tools import is_valid_resource_id
        if not is_valid_resource_id(namespace.assign_kubelet_identity):
            raise InvalidArgumentValueError("--assign-kubelet-identity is not a valid Azure resource ID.")


def validate_nodepool_id(namespace):
    from msrestazure.tools import is_valid_resource_id
    if not is_valid_resource_id(namespace.nodepool_id):
        raise InvalidArgumentValueError("--nodepool-id is not a valid Azure resource ID.")


def validate_snapshot_id(namespace):
    if namespace.snapshot_id:
        from msrestazure.tools import is_valid_resource_id
        if not is_valid_resource_id(namespace.snapshot_id):
            raise InvalidArgumentValueError("--snapshot-id is not a valid Azure resource ID.")


def validate_host_group_id(namespace):
    if namespace.host_group_id:
        from msrestazure.tools import is_valid_resource_id
        if not is_valid_resource_id(namespace.host_group_id):
            raise InvalidArgumentValueError("--host-group-id is not a valid Azure resource ID.")


def extract_comma_separated_string(
    raw_string,
    enable_strip=False,
    extract_kv=False,
    allow_empty_value=False,
    keep_none=False,
    default_value=None,
    allow_appending_values_to_same_key=False,
):
    """Extract comma-separated string.

    If enable_strip is specified, will remove leading and trailing whitespace before each operation on the string.
    If extract_kv is specified, will extract key value pairs from the string with "=" as the delimiter and this would
    return a dictionary, otherwise keep the entire string.
    Option allow_empty_value is valid since extract_kv is specified. When the number of string segments split by "="
    is 1, the first segment is retained as the key and empty string would be set as its corresponding value without
    raising an exception.
    Option allow_appending_values_to_same_key is valid since extract_kv is specified. For the same key, the new value
    is appended to the existing value separated by commas.
    If keep_none is specified, will return None when input is None. Otherwise will return default_value if input is
    None or empty string.
    """
    if raw_string is None:
        if keep_none:
            return None
        return default_value
    if enable_strip:
        raw_string = raw_string.strip()
    if raw_string == "":
        return default_value

    result = {} if extract_kv else []
    for item in raw_string.split(","):
        if enable_strip:
            item = item.strip()
        if extract_kv:
            kv_list = item.split("=")
            if len(kv_list) in [1, 2]:
                key = kv_list[0]
                value = ""
                if len(kv_list) == 2:
                    value = kv_list[1]
                if not allow_empty_value and (value == "" or value.isspace()):
                    raise InvalidArgumentValueError(
                        "Empty value not allowed. The value '{}' of key '{}' in '{}' is empty. Raw input '{}'.".format(
                            value, key, item, raw_string
                        )
                    )
                if enable_strip:
                    key = key.strip()
                    value = value.strip()
                if allow_appending_values_to_same_key and key in result:
                    value = "{},{}".format(result[key], value)
                result[key] = value
            else:
                raise InvalidArgumentValueError(
                    "The format of '{}' in '{}' is incorrect, correct format should be "
                    "'Key1=Value1,Key2=Value2'.".format(
                        item, raw_string
                    )
                )
        else:
            result.append(item)
    return result


def validate_credential_format(namespace):
    if namespace.credential_format and \
        namespace.credential_format.lower() != "azure" and \
            namespace.credential_format.lower() != "exec":
        raise InvalidArgumentValueError("--format can only be azure or exec.")


def validate_keyvault_secrets_provider_disable_and_enable_parameters(namespace):
    if namespace.disable_secret_rotation and namespace.enable_secret_rotation:
        raise MutuallyExclusiveArgumentError(
            "Providing both --disable-secret-rotation and --enable-secret-rotation flags is invalid"
        )


def validate_defender_config_parameter(namespace):
    if namespace.defender_config and not namespace.enable_defender:
        raise RequiredArgumentMissingError("Please specify --enable-defnder")


def validate_defender_disable_and_enable_parameters(namespace):
    if namespace.disable_defender and namespace.enable_defender:
        raise ArgumentUsageError('Providing both --disable-defender and --enable-defender flags is invalid')


def validate_azure_keyvault_kms_key_id(namespace):
    key_id = namespace.azure_keyvault_kms_key_id
    if key_id:
        # pylint:disable=line-too-long
        err_msg = '--azure-keyvault-kms-key-id is not a valid Key Vault key ID. See https://docs.microsoft.com/en-us/azure/key-vault/general/about-keys-secrets-certificates#vault-name-and-object-name'

        https_prefix = "https://"
        if not key_id.startswith(https_prefix):
            raise InvalidArgumentValueError(err_msg)

        segments = key_id[len(https_prefix):].split("/")
        if len(segments) != 4 or segments[1] != "keys":
            raise InvalidArgumentValueError(err_msg)


def validate_azure_keyvault_kms_key_vault_resource_id(namespace):
    key_vault_resource_id = namespace.azure_keyvault_kms_key_vault_resource_id
    if key_vault_resource_id is None or key_vault_resource_id == '':
        return
    from msrestazure.tools import is_valid_resource_id
    if not is_valid_resource_id(key_vault_resource_id):
        raise InvalidArgumentValueError("--azure-keyvault-kms-key-vault-resource-id is not a valid Azure resource ID.")


def validate_registry_name(cmd, namespace):
    """Append login server endpoint suffix."""
    registry = namespace.acr
    suffixes = cmd.cli_ctx.cloud.suffixes
    # Some clouds do not define 'acr_login_server_endpoint' (e.g. AzureGermanCloud)
    from azure.cli.core.cloud import CloudSuffixNotSetException
    try:
        acr_suffix = suffixes.acr_login_server_endpoint
    except CloudSuffixNotSetException:
        acr_suffix = None
    if registry and acr_suffix:
        pos = registry.find(acr_suffix)
        if pos == -1:
            logger.warning("The login server endpoint suffix '%s' is automatically appended.", acr_suffix)
            namespace.acr = registry + acr_suffix
