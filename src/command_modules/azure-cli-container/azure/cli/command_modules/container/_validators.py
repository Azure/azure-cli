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
