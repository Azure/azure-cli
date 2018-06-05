# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Verify all commands and arguments are loaded without errors. """


def init(root):
    parser = root.add_parser('load_all', help='Load the full command table, command arguments and help.')
    parser.set_defaults(func=verify_load_all)


def verify_load_all(_):
    from azure.cli.core import get_default_cli
    from azure.cli.core.file_util import get_all_help, create_invoker_and_load_cmds_and_args

    print('Loading all commands, arguments, and help...')
    # setup CLI to enable command loader
    az_cli = get_default_cli()

    # load commands, args, and help
    create_invoker_and_load_cmds_and_args(az_cli)
    loaded_help = get_all_help(az_cli)
    print('Everything loaded successfully.')
