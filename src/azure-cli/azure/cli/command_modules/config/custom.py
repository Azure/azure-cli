# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.prompting import prompt
from knack.util import CLIError

from azure.cli.core.util import ScopedConfig
from azure.cli.core.config_defaults import config

import azure.cli.core.telemetry as telemetry

logger = get_logger(__name__)


def _normalize_config_value(value):
    if value:
        value = '' if value in ["''", '""'] else value
    return value


def print_all_configs():
    print(f"\nDefault configuration sections: {[key for key in config]}\n")
    for section in config:
        print(f"\n{section}: ")
        for key in config[section].keys():
            print(f"\t {key}: {config[section][key]['description']}")


def list_available(cmd, key=None):
    selection_is_valid = False
    has_shown_configs = False

    if not key:
        print_all_configs()
        has_shown_configs = True
        key = prompt('\nEnter one of the above configuration keys (i.e. disable_confirmation_prompt)'
                     'to see its current, default, and available values.\nUse the form of <section>.<key> '
                     ' e.g. cloud.name. Leave blank to exit: ')

    # prompt user for input until valid
    while not selection_is_valid:
        if not key:
            # exit if empty string is entered
            raise CLIError('Operation cancelled.')

        key_arr = key.strip().split('.')

        if len(key_arr) != 2:
            key = prompt(f'\nInvalid entry <{key}>. \nEnter in the form of '
                         '<section>.<key> e.g. cloud.name. Leave blank to exit: ')
        else:
            selected_section = key_arr[0]
            selected_key = key_arr[1]
            if selected_section in config and selected_key in config[selected_section]:
                selection_is_valid = True
            else:
                # if we haven't already show all of the configs, do so now
                if not has_shown_configs:
                    print_all_configs()
                    has_shown_configs = True

                key = prompt(f'\nConfig default not found: {selected_section}.{selected_key}. '
                             '\nEnter in the form of <section>.<key> e.g. cloud.name. '
                             'Leave blank to exit:  ')

    config_value = config[selected_section][selected_key]
    current_value = {}
    try:
        current_value = config_get(cmd, f"{selected_section}.{selected_key}")
    except CLIError:
        # value not set in config, treat it as default
        current_value['value'] = config_value['default']

    if config_value["allowed"]:
        allowed_values = [elem['value'] for elem in config_value['allowed']]
    else:
        # for options that are limited by type i.e. string/integer
        allowed_values = config_value['type']

    return {
        "Key": selected_key,
        "Current": current_value['value'],
        "Default": config_value['default'],
        "Allowed": allowed_values,
        "Section": selected_section
    }


def config_set(cmd, key_value=None, local=False):
    if key_value:
        with ScopedConfig(cmd.cli_ctx.config, local):
            telemetry_contents = []
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
                telemetry_contents.append((key, section, value))
            telemetry.set_debug_info('ConfigSet', telemetry_contents)


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
    telemetry.set_debug_info('ConfigUnset', ' '.join(key))


def turn_param_persist_on(cmd):
    if not cmd.cli_ctx.local_context.is_on:
        cmd.cli_ctx.local_context.turn_on()
        logger.warning('Parameter persistence is turned on, you can run `az config param-persist off` to turn it off.')
    else:
        logger.warning('Parameter persistence is on already.')


def turn_param_persist_off(cmd):
    if cmd.cli_ctx.local_context.is_on:
        cmd.cli_ctx.local_context.turn_off()
        logger.warning('Parameter persistence is turned off, you can run `az config param-persist on` to turn it on.')
    else:
        logger.warning('Parameter persistence is off already.')


def show_param_persist(cmd, name=None):
    if not name:
        name = None
    return cmd.cli_ctx.local_context.get_value(name)


def delete_param_persist(cmd, name=None, all=False, yes=False, purge=False, recursive=False):  # pylint: disable=redefined-builtin
    if name:
        cmd.cli_ctx.local_context.delete(name)

    if all:
        from azure.cli.core.util import user_confirmation
        if purge:
            user_confirmation('You are going to delete parameter persistence file. '
                              'Are you sure you want to continue this operation ?', yes)
            cmd.cli_ctx.local_context.delete_file(recursive)
        else:
            user_confirmation('You are going to clear all parameter persistence values. '
                              'Are you sure you want to continue this operation ?', yes)
            cmd.cli_ctx.local_context.clear(recursive)
