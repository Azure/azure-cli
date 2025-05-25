# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

_config_section = "bicep"

_use_binary_from_path_config_key = "use_binary_from_path"
_use_binary_from_path_config_default_value = "if_found_in_ci"

_check_version_config_key = "check_version"
_check_version_config_default_value = True


def get_use_binary_from_path_config(cli_ctx):
    return cli_ctx.config.get(
        _config_section, _use_binary_from_path_config_key, _use_binary_from_path_config_default_value
    ).lower()


def set_use_binary_from_path_config(cli_ctx, value):
    cli_ctx.config.set_value(_config_section, _use_binary_from_path_config_key, value)


def remove_use_binary_from_path_config(cli_ctx):
    cli_ctx.config.remove_option(_config_section, _use_binary_from_path_config_key)


def get_check_version_config(cli_ctx):
    return cli_ctx.config.getboolean(_config_section, _check_version_config_key, _check_version_config_default_value)
