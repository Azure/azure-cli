# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError

from azure.cli.core.util import ScopedConfig

logger = get_logger(__name__)


def _normalize_config_value(value):
    if value:
        value = '' if value in ["''", '""'] else value
    return value


def config_set(cmd, key_value=None, local=False):
    if key_value:
        with ScopedConfig(cmd.cli_ctx.config, local):
            for kv in key_value:
                # core.no_color=true
                parts = kv.split('=', 1)
                if len(parts) == 1:
                    raise CLIError('usage error: [section].[name]=[value] ...')
                key = parts[0]
                value = parts[1]

                # core.no_color
                parts = key.split('.', 1)
                if len(parts) == 1:
                    raise CLIError('usage error: [section].[name]=[value] ...')
                section = parts[0]
                name = parts[1]

                cmd.cli_ctx.config.set_value(section, name, _normalize_config_value(value))


def config_get(cmd, key=None, local=False):
    # No arg. List all sections and all items
    if not key:
        with ScopedConfig(cmd.cli_ctx.config, local):
            sections = cmd.cli_ctx.config.sections()
            result = {}
            for section in sections:
                items = cmd.cli_ctx.config.items(section)
                result[section] = items
            return result

    parts = key.split('.', 1)
    if len(parts) == 1:
        # Only section is provided
        section = key
        name = None
    else:
        # section.name
        section = parts[0]
        name = parts[1]

    with ScopedConfig(cmd.cli_ctx.config, local):
        items = cmd.cli_ctx.config.items(section)

    if not name:
        # Only section
        return items

    # section.option
    try:
        return next(x for x in items if x['name'] == name)
    except StopIteration:
        raise CLIError("Configuration '{}' is not set.".format(key))


def config_unset(cmd, key=None, local=False):
    for k in key:
        # section.name
        parts = k.split('.', 1)

        if len(parts) == 1:
            raise CLIError("usage error: [section].[name]")

        section = parts[0]
        name = parts[1]

        with ScopedConfig(cmd.cli_ctx.config, local):
            cmd.cli_ctx.config.remove_option(section, name)
