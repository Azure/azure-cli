# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Verify all commands and arguments are loaded without errors. """


FAILED_TO_LOAD = []
EXTENSION_FAILURE_EXCLUSIONS = []

def init(root):
    parser = root.add_parser('load-all', help='Load the full command table, command arguments and help.')
    parser.set_defaults(func=verify_load_all)


def verify_load_all(_):
    from azure.cli.core import get_default_cli, EVENT_FAILED_EXTENSION_LOAD
    from azure.cli.core.file_util import get_all_help, create_invoker_and_load_cmds_and_args

    print('Loading all commands, arguments, and help...')
    # setup CLI to enable command loader and register event
    az_cli = get_default_cli()
    az_cli.register_event(EVENT_FAILED_EXTENSION_LOAD, extension_failed_load_handler)

    # load commands, args, and help
    create_invoker_and_load_cmds_and_args(az_cli)
    loaded_help = get_all_help(az_cli)

    # verify each installed extension is properly loaded
    if not FAILED_TO_LOAD or set(FAILED_TO_LOAD).issubset(set(EXTENSION_FAILURE_EXCLUSIONS)):
        print('Everything loaded successfully.')
    else:
        raise Exception('Exceptions failed to load: {}'.format(', '.join(FAILED_TO_LOAD)))

def extension_failed_load_handler(_, **kwargs):
    FAILED_TO_LOAD.append(kwargs.get('extension_name'))
