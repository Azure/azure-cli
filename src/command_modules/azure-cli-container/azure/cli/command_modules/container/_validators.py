# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from base64 import b64encode
from knack.util import CLIError


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


def validate_subnet(ns):
    from msrestazure.tools import is_valid_resource_id

    if not is_valid_resource_id(ns.subnet) and ((ns.vnet_name and not ns.subnet) or (ns.subnet and not ns.vnet_name)):
        raise CLIError('usage error: --vnet-name NAME --subnet NAME | --subnet ID')


def validate_network_profile(cmd, ns):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id

    if ns.network_profile and ns.ip_address:
        raise CLIError('Can not use "--network-profile" with IP address type "Public".')
    elif ns.network_profile and ns.dns_name_label:
        raise CLIError('Can not use "--network-profile" with "--dns-name-label".')
    elif ns.network_profile:
        if not is_valid_resource_id(ns.network_profile):
            ns.network_profile = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=ns.resource_group_name,
                namespace='Microsoft.Network', type='networkProfiles',
                name=ns.network_profile
            )
