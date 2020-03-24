# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import unicode_literals
import os
import os.path
import re
from math import ceil
from ipaddress import ip_network

# pylint: disable=no-name-in-module,import-error
from knack.log import get_logger

from azure.cli.core.commands.validators import validate_tag
from azure.cli.core.util import CLIError
import azure.cli.core.keys as keys

logger = get_logger(__name__)


def validate_connector_name(namespace):
    """Validates a string as a legal connector name.

    This validation will also occur server-side in the kubernetes, but that may take
    for a while. So it's more user-friendly to validate in the CLI pre-flight.
    """
    # https://github.com/kubernetes/community/blob/master/contributors/design-proposals/architecture/identifiers.md
    regex = re.compile(r'^[a-z0-9]([a-z0-9\-]*[a-z0-9])?$')
    found = regex.findall(namespace.connector_name)
    if not found:
        raise CLIError('--connector-name must consist of lower case alphanumeric characters or dashes (-), '
                       'and must start and end with alphanumeric characters.')


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


def validate_list_of_integers(string):
    # extract comma-separated list of integers
    return list(map(int, string.split(',')))


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
        k8s_release_regex = re.compile(r'^[v|V]?(\d+\.\d+\.\d+.*)$')
        found = k8s_release_regex.findall(namespace.kubernetes_version)
        if found:
            namespace.kubernetes_version = found[0]
        else:
            raise CLIError('--kubernetes-version should be the full version number, '
                           'such as "1.11.8" or "1.12.6"')


def validate_nodepool_name(namespace):
    """Validates a nodepool name to be at most 12 characters, alphanumeric only."""
    if namespace.nodepool_name != "":
        if len(namespace.nodepool_name) > 12:
            raise CLIError('--nodepool-name can contain at most 12 characters')
        if not namespace.nodepool_name.isalnum():
            raise CLIError('--nodepool-name should contain only alphanumeric characters')


def validate_k8s_client_version(namespace):
    """Validates a string as a possible Kubernetes version."""
    k8s_release_regex = re.compile(r'^[v|V]?(\d+\.\d+\.\d+.*|latest)$')
    found = k8s_release_regex.findall(namespace.client_version)
    if found:
        namespace.client_version = found[0]
    else:
        raise CLIError('--client-version should be the full version number '
                       '(such as "1.11.8" or "1.12.6") or "latest"')


def validate_linux_host_name(namespace):
    """Validates a string as a legal host name component.

    This validation will also occur server-side in the ARM API, but that may take
    a minute or two before the user sees it. So it's more user-friendly to validate
    in the CLI pre-flight.
    """
    # https://stackoverflow.com/questions/106179/regular-expression-to-match-dns-hostname-or-ip-address
    rfc1123_regex = re.compile(r'^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])(\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]))*$')  # pylint:disable=line-too-long
    found = rfc1123_regex.findall(namespace.name)
    if not found:
        raise CLIError('--name cannot exceed 63 characters and can only contain '
                       'letters, numbers, or dashes (-).')


def validate_max_pods(namespace):
    """Validates that max_pods is set to a reasonable minimum number."""
    # kube-proxy and kube-svc reside each nodes,
    # 2 kube-proxy pods, 1 azureproxy/heapster/dashboard/tunnelfront are in kube-system
    minimum_pods_required = ceil((namespace.node_count * 2 + 6 + 1) / namespace.node_count)
    if namespace.max_pods != 0 and namespace.max_pods < minimum_pods_required:
        raise CLIError('--max-pods must be at least {} for a managed Kubernetes cluster to function.'
                       .format(minimum_pods_required))


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
        if namespace.load_balancer_idle_timeout < 4 or namespace.load_balancer_idle_timeout > 120:
            raise CLIError("--load-balancer-idle-timeout must be in the range [4,120]")


def validate_nodes_count(namespace):
    """Validates that min_count and max_count is set between 1-100"""
    if namespace.min_count is not None:
        if namespace.min_count < 1 or namespace.min_count > 100:
            raise CLIError('--min-count must be in the range [1,100]')
    if namespace.max_count is not None:
        if namespace.max_count < 1 or namespace.max_count > 100:
            raise CLIError('--max-count must be in the range [1,100]')


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
    if namespace.vnet_subnet_id is not None:
        if namespace.vnet_subnet_id == '':
            return
        from msrestazure.tools import is_valid_resource_id
        if not is_valid_resource_id(namespace.vnet_subnet_id):
            raise CLIError("--vnet-subnet-id is not a valid Azure resource ID.")


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
        raise CLIError("Invalid label: %s. Label must be more than 63 chars." % label)
    if not value_regex.match(kv[1]):
        raise CLIError("Invalid label: %s. A valid label must be an empty string or consist of alphanumeric "
                       "characters, '-', '_' or '.', and must start and end with an alphanumeric character" % label)

    return {kv[0]: kv[1]}
