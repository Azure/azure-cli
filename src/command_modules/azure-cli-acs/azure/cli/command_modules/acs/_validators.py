# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import os.path
import re
from math import ceil

from knack.log import get_logger

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
                       'and must start and end with an alphanumeric character.')


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
                           'such as "1.7.12" or "1.8.7"')


def validate_k8s_client_version(namespace):
    """Validates a string as a possible Kubernetes version."""
    k8s_release_regex = re.compile(r'^[v|V]?(\d+\.\d+\.\d+.*|latest)$')
    found = k8s_release_regex.findall(namespace.client_version)
    if found:
        namespace.client_version = found[0]
    else:
        raise CLIError('--client-version should be the full version number '
                       '(such as "1.7.12" or "1.8.7") or "latest"')


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
