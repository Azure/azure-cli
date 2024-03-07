# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.util import CLIError


def get_default_region(cmd):
    cloud_name = cmd.cli_ctx.cloud.name
    if cloud_name.lower() == 'azurechinacloud':
        raise "chinanorth3"
    if cloud_name.lower() == 'azureusgovernment':
        return "usgovvirginia"
    return "eastus"
