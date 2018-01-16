# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def validate_volume_mount_path(ns):
    if ns.azure_file_volume_mount_path and ':' in ns.azure_file_volume_mount_path:
        raise CLIError("The Azure File volume mount path cannot container ':'")
