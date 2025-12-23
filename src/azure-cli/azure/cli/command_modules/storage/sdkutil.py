# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Assist the command module to get correct type from SDK based on current API version"""

from azure.cli.core.profiles import get_sdk, ResourceType


def get_blob_types():
    return 'block', 'page', 'append'


def get_blob_tier_names_track2(cli_ctx, model_path):
    t_blob_tier_model = get_sdk(cli_ctx, ResourceType.DATA_STORAGE_BLOB, model_path)
    return [v for v in dir(t_blob_tier_model) if not v.startswith('_')]


def get_delete_blob_snapshot_type_names():
    return 'include', 'only'


def get_container_access_type_names():
    return 'off', 'blob', 'container'


def get_fs_access_type_names():
    return 'off', 'file', 'filesystem'


def get_fs_access_type(cli_ctx, name):
    if name == 'off':
        return None
    if name == 'file':
        return get_sdk(cli_ctx, ResourceType.DATA_STORAGE_FILEDATALAKE, 'PublicAccess', mod='_models').File
    if name == 'filesystem':
        return get_sdk(cli_ctx, ResourceType.DATA_STORAGE_FILEDATALAKE, 'PublicAccess', mod='_models').FileSystem
    raise KeyError


def get_blob_sync_delete_destination_types():
    return 'true', 'false', 'prompt'
