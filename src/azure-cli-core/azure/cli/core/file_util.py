# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from knack.util import CLIError
from knack.help import GroupHelpFile

from azure.cli.core._help import CliCommandHelpFile


def get_all_help(cli_ctx):
    invoker = cli_ctx.invocation
    help_ctx = cli_ctx.help_cls(cli_ctx)
    if not invoker:
        raise CLIError('CLI context does not contain invocation.')

    parser_keys = []
    parser_values = []
    sub_parser_keys = []
    sub_parser_values = []
    _store_parsers(invoker.parser, parser_keys, parser_values, sub_parser_keys, sub_parser_values)
    for cmd, parser in zip(parser_keys, parser_values):
        if cmd not in sub_parser_keys:
            sub_parser_keys.append(cmd)
            sub_parser_values.append(parser)
    help_files = []
    for cmd, parser in zip(sub_parser_keys, sub_parser_values):
        try:
            help_file = GroupHelpFile(help_ctx, cmd, parser) if _is_group(parser) \
                else CliCommandHelpFile(help_ctx, cmd, parser)
            help_file.load(parser)
            help_files.append(help_file)
        except Exception as ex:  # pylint: disable=broad-except
            print("Skipped '{}' due to '{}'".format(cmd, ex))
    help_files = sorted(help_files, key=lambda x: x.command)
    return help_files


def create_invoker_and_load_cmds_and_args(cli_ctx):
    from knack import events
    from azure.cli.core.commands.arm import register_global_subscription_argument, register_ids_argument

    invoker = cli_ctx.invocation_cls(cli_ctx=cli_ctx, commands_loader_cls=cli_ctx.commands_loader_cls,
                                     parser_cls=cli_ctx.parser_cls, help_cls=cli_ctx.help_cls)
    cli_ctx.invocation = invoker
    invoker.commands_loader.skip_applicability = True
    invoker.commands_loader.load_command_table(None)

    # turn off applicability check for all loaders
    for loaders in invoker.commands_loader.cmd_to_loader_map.values():
        for loader in loaders:
            loader.skip_applicability = True

    for command in invoker.commands_loader.command_table:
        invoker.commands_loader.load_arguments(command)

    register_global_subscription_argument(cli_ctx)
    register_ids_argument(cli_ctx)  # global subscription must be registered first!
    cli_ctx.raise_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, commands_loader=invoker.commands_loader)
    invoker.parser.load_command_table(invoker.commands_loader)


def _store_parsers(parser, parser_keys, parser_values, sub_parser_keys, sub_parser_values):
    for s in parser.subparsers.values():
        parser_keys.append(_get_parser_name(s))
        parser_values.append(s)
        if _is_group(s):
            for c in s.choices.values():
                sub_parser_keys.append(_get_parser_name(c))
                sub_parser_values.append(c)
                _store_parsers(c, parser_keys, parser_values, sub_parser_keys, sub_parser_values)


def _get_parser_name(s):
    return (s._prog_prefix if hasattr(s, '_prog_prefix') else s.prog)[3:]  # pylint: disable=protected-access


def _is_group(parser):
    return getattr(parser, '_subparsers', None) is not None \
        or getattr(parser, 'choices', None) is not None
