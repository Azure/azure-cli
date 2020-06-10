# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from base64 import b64encode
from knack.util import CLIError
from knack.log import get_logger

logger = get_logger(__name__)

short_running_images = ['alpine', 'busybox', 'ubuntu', 'node', 'golang', 'centos', 'python', 'php']


def validate_volume_mount_path(ns):
    if ns.azure_file_volume_mount_path and ':' in ns.azure_file_volume_mount_path:
        raise CLIError("The volume mount path cannot contain ':'")


def validate_secrets(ns):
    """ Extracts multiple space-separated secrets in key=value format """
    if isinstance(ns.secrets, list):
        secrets_dict = {}
        for item in ns.secrets:
            secrets_dict.update(validate_secret(item))
        ns.secrets = secrets_dict


def validate_secret(string):
    """ Extracts a single secret in key=value format """
    result = {}
    if string:
        comps = string.split('=', 1)
        if len(comps) != 2:
            raise CLIError("Secrets need to be specifed in key=value format.")
        result = {comps[0]: b64encode(comps[1].encode('ascii')).decode('ascii')}
    return result


def validate_gitrepo_directory(ns):
    if ns.gitrepo_dir and '..' in ns.gitrepo_dir:
        raise CLIError("The git repo directory cannot contain '..'")


def validate_image(ns):
    if ns.image and ns.image.split(':')[0] in short_running_images and not ns.command_line:
        logger.warning('Image "%s" has no long running process. The "--command-line" argument must be used to start a '
                       'long running process inside the container for the container group to stay running. '
                       'Ex: "tail -f /dev/null" '
                       'For more imformation visit https://aka.ms/aci/troubleshoot',
                       ns.image)


def validate_msi(namespace):
    MSI_LOCAL_ID = '[system]'
    if namespace.assign_identity is not None:
        identities = namespace.assign_identity or []
        if not namespace.identity_scope and getattr(namespace.identity_role, 'is_default', None) is None:
            raise CLIError("usage error: '--role {}' is not applicable as the '--scope' is not provided".format(
                namespace.identity_role))

        if namespace.identity_scope:
            if identities and MSI_LOCAL_ID not in identities:
                raise CLIError("usage error: '--scope'/'--role' is only applicable when assign system identity")

    elif namespace.identity_scope or getattr(namespace.identity_role, 'is_default', None) is None:
        raise CLIError('usage error: --assign-identity [--scope SCOPE] [--role ROLE]')


def validate_subnet(ns):
    from msrestazure.tools import is_valid_resource_id

    # vnet_name is depricated, using for backwards compatability
    if ns.vnet_name and not ns.vnet:
        ns.vnet = ns.vnet_name

    if not is_valid_resource_id(ns.subnet) and ((ns.vnet and not ns.subnet) or (ns.subnet and not ns.vnet)):
        raise CLIError('usage error: --vnet NAME --subnet NAME | --vnet ID --subnet NAME | --subnet ID')


def validate_network_profile(cmd, ns):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id

    if ns.network_profile and ns.ip_address:
        raise CLIError('Can not use "--network-profile" with IP address type "Public".')
    if ns.network_profile and ns.dns_name_label:
        raise CLIError('Can not use "--network-profile" with "--dns-name-label".')
    if ns.network_profile:
        if not is_valid_resource_id(ns.network_profile):
            ns.network_profile = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=ns.resource_group_name,
                namespace='Microsoft.Network', type='networkProfiles',
                name=ns.network_profile
            )
