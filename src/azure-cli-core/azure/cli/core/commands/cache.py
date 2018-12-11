# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import timeit

from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.extension import get_extensions
from azure.cli.core._environment import get_config_dir

logger = get_logger(__name__)


CACHE_FILE = os.path.join(get_config_dir(), 'command_module_index')
VERSION_STR = "VERSION"
EXTENSIONS_STR = "EXTENSIONS"
EXTENSIONS_LIST = ["{}-{}".format(ext.name, ext.version) for ext in get_extensions()]


# return true if the cache exists and caching is enabled.
def cache_exists():
    use_cache = os.path.isfile(CACHE_FILE) and os.getenv('AZ_USE_CACHE', 'False').lower() == 'true'
    logger.debug('use_cache is %s', use_cache)
    return use_cache


def cache_command_table(cli_ctx, cmd_to_loader_map):
    try:
        with open(CACHE_FILE, 'w') as f_cache:
            f_cache.write("{},{}\n".format(VERSION_STR, cli_ctx.get_cli_version()))
            f_cache.write("{},{}\n".format(EXTENSIONS_STR, ",".join(EXTENSIONS_LIST)))
            for cmd, loader in cmd_to_loader_map.items():
                f_cache.write("{},{}\n".format(cmd, loader[0].__class__.__module__))
            logger.warning("Wrote command index to %s", CACHE_FILE)

    except IOError:
        raise CLIError("Error: Failed to cache command index.")

    logger.debug("Updated command module index cache in %s", CACHE_FILE)
    return CACHE_FILE


# clear the cache by deleting it.
def clear_cache():
    if os.path.isfile(CACHE_FILE):
        os.remove(CACHE_FILE)


# TODO: this needs to handle extensions as well....
def load_command_table(main_loader, args):
    start_time = timeit.default_timer()
    from azure.cli.core.commands import _load_module_command_loader

    current_cli_version = main_loader.cli_ctx.get_cli_version()
    cmd_to_mod_name = {}
    try:
        with open(CACHE_FILE, mode='r') as f_cache:
            for line in f_cache:
                line_item = line.strip().split(",")
                cmd_to_mod_name[line_item[0]] = line_item[1].split(".")[-1]
                # check the CLI version
                if line_item[0] == VERSION_STR and line_item[1] != current_cli_version:
                    logger.debug("Command index cache CLI version does not match current CLI version.")
                    return None
                if line_item[0] == EXTENSIONS_STR:  # todo: Consider optimizing this for non-extensions?
                    cached_extensions_set = set(line_item[1:])
                    installed_extensions_set = set(EXTENSIONS_LIST)
                    if cached_extensions_set != installed_extensions_set:
                        msg = "Command index cache extensions list does not match installed extensions:" \
                              "\n\tCached extensions %s\n\tInstalled extensions %s"
                        logger.debug(msg, cached_extensions_set, installed_extensions_set)
                        return None
    except IOError:
        logger.warning("Error opening cache.")
        return None

    command = _rudimentary_get_command(cmd_to_mod_name.keys(), args)

    module_name = cmd_to_mod_name.get(command)

    if not module_name:
        return None

    module_command_table, module_group_table = _load_module_command_loader(main_loader, args, module_name)
    for cmd in module_command_table.values():
        cmd.command_source = module_name

    main_loader.command_table.update(module_command_table)
    main_loader.command_group_table.update(module_group_table)

    elapsed_time = timeit.default_timer() - start_time
    logger.debug("Loaded relevant module' in %.3f seconds.", elapsed_time)

    return main_loader.command_table


def _rudimentary_get_command(command_names, args):  # pylint: disable=no-self-use
    """ Rudimentary parsing to get the command """
    nouns = []
    for arg in args:
        if arg and arg[0] != '-':
            nouns.append(arg)
        else:
            break

    def _find_args(args):
        search = ' '.join(args)
        return next((x for x in command_names if x.startswith(search)), False)

    # since the command name may be immediately followed by a positional arg, strip those off
    while nouns and not _find_args(nouns):
        del nouns[-1]
    return ' '.join(nouns)
