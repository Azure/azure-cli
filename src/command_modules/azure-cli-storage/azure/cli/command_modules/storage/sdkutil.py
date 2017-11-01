# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Assist the command module to get correct type from SDK based on current API version"""

from azure.cli.core.profiles import get_sdk, supported_api_version, ResourceType
from azure.cli.core.profiles._shared import APIVersionException


def cosmosdb_table_exists(cli_ctx):
    try:
        return supported_api_version(cli_ctx, ResourceType.DATA_COSMOS_TABLE, min_api='2017-04-17')
    except APIVersionException:
        return False


def get_table_data_type(cli_ctx, module_name, *type_names):
    if cosmosdb_table_exists(cli_ctx):
        return get_sdk(cli_ctx, ResourceType.DATA_COSMOS_TABLE, *type_names, mod=module_name)

    return get_sdk(cli_ctx, ResourceType.DATA_STORAGE, *type_names, mod=module_name)
