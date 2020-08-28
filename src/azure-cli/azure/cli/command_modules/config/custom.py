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


def _parse_key(key):
    """Parse the key to section and option name. There can be 2 case:
        1. If no section is provided, like `no_color`, section will default to `core`.
        2. If section is provided, like `core.no_color`, use the specified section.
    """
    if not key:
        raise ValueError
    parts = key.split('.', 1)
    if len(parts) == 1:
        # Section is not provided, default to `core`
        return 'core', key
    # Section is provided, like `core.no_color`, use the specified section.
    return parts[0], parts[1]


def config_set(cmd, key_value_pairs=None, local=False):
    with ScopedConfig(cmd.cli_ctx.config, local):
        for kv in key_value_pairs:
            # core.no_color=true
            parts = kv.split('=', 1)
            if len(parts) == 1:
                raise CLIError('usage error: [section].[name]=[value] ...')
            key = parts[0]
            value = parts[1]

            try:
                section, name = _parse_key(key)
            except ValueError:
                raise CLIError('usage error: [section].[name]=[value] ...')

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

    section, name = _parse_key(key)

    with ScopedConfig(cmd.cli_ctx.config, local):
        items = cmd.cli_ctx.config.items(section)

    if not name:
        # Only section
        return items

    # section.option
    try:
        return next(x for x in items if x['name'] == name)
    except StopIteration:
        raise CLIError("Configuration '{}.{}' is not set.".format(section, name))


def config_unset(cmd, keys=None, local=False):
    for key in keys:
        # section.name
        try:
            section, name = _parse_key(key)
        except ValueError:
            raise CLIError("usage error: [section].[name]")

        with ScopedConfig(cmd.cli_ctx.config, local):
            cmd.cli_ctx.config.remove_option(section, name)
