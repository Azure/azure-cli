# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import timeit

from knack.log import get_logger
logger = get_logger(__name__)


from automation.utilities.path import get_repo_root
CACHE_FILE = os.path.join(get_repo_root(), '.cache.txt')


def cache_exists():
    use_cache = os.path.isfile(CACHE_FILE) and os.getenv('AZ_USE_CACHE', 'False').lower() == 'true'
    print('use_cache is {}'.format(use_cache))
    return use_cache

def persist_command_table(cmd_to_loader_map):
    if not os.path.isfile(CACHE_FILE):
        with open('.cache.txt', 'w') as f_cache:
            for cmd, loader in cmd_to_loader_map.items():
                f_cache.write("{},{}\n".format(cmd, loader[0].__class__.__module__))

    return CACHE_FILE

# TODO: this needs to handle extensions as well....
def load_command_table(main_loader, args):
    start_time = timeit.default_timer()
    from azure.cli.core.commands import _load_module_command_loader

    cmd_to_mod_name = {}
    try:
        with open(CACHE_FILE, mode='r') as f_cache:
            for line in f_cache:
                line_item = line.strip().split(",")
                cmd_to_mod_name[line_item[0]] = line_item[1].split(".")[-1]
    except IOError:
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
    logger.debug("Loaded relevant modules' in %.3f seconds.", elapsed_time)

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
