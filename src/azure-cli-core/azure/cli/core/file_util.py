# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

from azure.cli.core._help import CliCommandHelpFile, CliGroupHelpFile

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


def get_all_help(cli_ctx, skip=True):
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
    help_errors = {}
    for cmd, parser in zip(sub_parser_keys, sub_parser_values):
        try:
            help_ctx.update_loaders_with_help_file_contents(cmd.split())
            help_file = CliGroupHelpFile(help_ctx, cmd, parser) if _is_group(parser) \
                else CliCommandHelpFile(help_ctx, cmd, parser)
            help_file.load(parser)
            help_files.append(help_file)
        except Exception as ex:  # pylint: disable=broad-except
            if skip:
                logger.warning("Skipping '%s': %s", cmd, ex)
            else:
                help_errors[cmd] = "Error '{}': {}".format(cmd, ex)
    if help_errors:
        raise CLIError(help_errors)
    help_files = sorted(help_files, key=lambda x: x.command)
    return help_files


def create_invoker_and_load_cmds_and_args(cli_ctx):
    from knack.events import (
        EVENT_INVOKER_PRE_CMD_TBL_CREATE, EVENT_INVOKER_POST_CMD_TBL_CREATE)
    from azure.cli.core.commands import register_cache_arguments
    from azure.cli.core.commands.arm import register_global_subscription_argument, register_ids_argument
    from azure.cli.core.commands.events import (
        EVENT_INVOKER_PRE_LOAD_ARGUMENTS, EVENT_INVOKER_POST_LOAD_ARGUMENTS)
    import time

    start_time = time.time()

    register_global_subscription_argument(cli_ctx)
    register_ids_argument(cli_ctx)
    register_cache_arguments(cli_ctx)

    invoker = cli_ctx.invocation_cls(cli_ctx=cli_ctx, commands_loader_cls=cli_ctx.commands_loader_cls,
                                     parser_cls=cli_ctx.parser_cls, help_cls=cli_ctx.help_cls)
    cli_ctx.invocation = invoker
    invoker.commands_loader.skip_applicability = True

    cli_ctx.raise_event(EVENT_INVOKER_PRE_CMD_TBL_CREATE, args=[])
    invoker.commands_loader.load_command_table(None)
    invoker.commands_loader.command_name = ''

    cli_ctx.raise_event(EVENT_INVOKER_PRE_LOAD_ARGUMENTS, commands_loader=invoker.commands_loader)
    invoker.commands_loader.load_arguments()

    cli_ctx.raise_event(EVENT_INVOKER_POST_LOAD_ARGUMENTS, commands_loader=invoker.commands_loader)
    cli_ctx.raise_event(EVENT_INVOKER_POST_CMD_TBL_CREATE, commands_loader=invoker.commands_loader)
    invoker.parser.cli_ctx = cli_ctx
    invoker.parser.load_command_table(invoker.commands_loader)

    end_time = time.time()
    logger.info('Time to load entire command table: %.3f sec', end_time - start_time)


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
