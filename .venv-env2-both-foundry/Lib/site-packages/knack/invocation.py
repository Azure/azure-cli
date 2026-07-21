# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
from collections import defaultdict

from .commands import CLICommandsLoader
from .deprecation import ImplicitDeprecated, resolve_deprecate_info
from .events import (EVENT_INVOKER_PRE_CMD_TBL_CREATE, EVENT_INVOKER_POST_CMD_TBL_CREATE,
                     EVENT_INVOKER_CMD_TBL_LOADED, EVENT_INVOKER_PRE_PARSE_ARGS,
                     EVENT_INVOKER_POST_PARSE_ARGS, EVENT_INVOKER_TRANSFORM_RESULT,
                     EVENT_INVOKER_FILTER_RESULT)
from .experimental import ImplicitExperimentalItem, resolve_experimental_info
from .help import CLIHelp
from .log import CLILogging
from .parser import CLICommandParser
from .preview import ImplicitPreviewItem, resolve_preview_info
from .util import CLIError, CtxTypeError, CommandResultItem, todict


class CommandInvoker(object):

    def __init__(self,
                 cli_ctx=None,
                 parser_cls=CLICommandParser,
                 commands_loader_cls=CLICommandsLoader,
                 help_cls=CLIHelp,
                 initial_data=None):
        """ Manages a single invocation of the CLI (i.e. running a command)

        :param cli_ctx: CLI Context
        :type cli_ctx: knack.cli.CLI
        :param parser_cls: A class to handle command parsing
        :type parser_cls: knack.parser.CLICommandParser
        :param commands_loader_cls: A class to handle loading commands
        :type commands_loader_cls: knack.commands.CLICommandsLoader
        :param help_cls: A class to handle help
        :type help_cls: knack.help.CLIHelp
        :param initial_data: The initial in-memory collection for this command invocation
        :type initial_data: dict
        """
        from .cli import CLI
        if cli_ctx is not None and not isinstance(cli_ctx, CLI):
            raise CtxTypeError(cli_ctx)
        self.cli_ctx = cli_ctx
        # In memory collection of key-value data for this current invocation This does not persist between invocations.
        self.data = initial_data or defaultdict(lambda: None)
        self.data['command'] = 'unknown'
        self._global_parser = parser_cls.create_global_parser(cli_ctx=self.cli_ctx)
        self.help = help_cls(cli_ctx=self.cli_ctx)
        self.parser = parser_cls(cli_ctx=self.cli_ctx, cli_help=self.help,
                                 prog=self.cli_ctx.name, parents=[self._global_parser])
        self.commands_loader = commands_loader_cls(cli_ctx=self.cli_ctx)

    def _filter_params(self, args):
        # Consider - we are using any args that start with an underscore (_) as 'private'
        # arguments and remove them from the arguments that we pass to the actual function.
        params = {key: value
                  for key, value in args.__dict__.items()
                  if not key.startswith('_')}
        params.pop('func', None)
        params.pop('command', None)
        return params

    def _rudimentary_get_command(self, args):
        """ Rudimentary parsing to get the command """
        nouns = []
        command_names = self.commands_loader.command_table.keys()
        for arg in args:
            if arg and arg[0] != '-':
                nouns.append(arg)
            else:
                break

        def _find_args(args):
            search = ' '.join(args).lower()
            return next((x for x in command_names if x.startswith(search)), False)

        # since the command name may be immediately followed by a positional arg, strip those off
        while nouns and not _find_args(nouns):
            del nouns[-1]

        # ensure the command string is case-insensitive
        for i in range(len(nouns)):
            args[i] = args[i].lower()

        return ' '.join(nouns)

    def _validate_cmd_level(self, ns, cmd_validator):
        if cmd_validator:
            cmd_validator(ns)
        try:
            delattr(ns, '_command_validator')
        except AttributeError:
            pass

    def _validate_arg_level(self, ns, **_):
        for validator in getattr(ns, '_argument_validators', []):
            validator(ns)
        try:
            delattr(ns, '_argument_validators')
        except AttributeError:
            pass

    def _validation(self, parsed_ns):
        try:
            cmd_validator = getattr(parsed_ns, '_command_validator', None)
            if cmd_validator:
                self._validate_cmd_level(parsed_ns, cmd_validator)
            else:
                self._validate_arg_level(parsed_ns)
        except CLIError:
            raise
        except Exception:  # pylint: disable=broad-except
            err = sys.exc_info()[1]
            getattr(parsed_ns, '_parser', self.parser).validation_error(str(err))

    # pylint: disable=too-many-statements
    def execute(self, args):
        """ Executes the command invocation

        :param args: The command arguments for this invocation
        :type args: list
        :return: The command result
        :rtype: knack.util.CommandResultItem
        """

        self.cli_ctx.raise_event(EVENT_INVOKER_PRE_CMD_TBL_CREATE, args=args)
        cmd_tbl = self.commands_loader.load_command_table(args)
        command = self._rudimentary_get_command(args)
        self.cli_ctx.invocation.data['command_string'] = command
        self.commands_loader.load_arguments(command)

        self.cli_ctx.raise_event(EVENT_INVOKER_POST_CMD_TBL_CREATE, cmd_tbl=cmd_tbl)
        self.parser.load_command_table(self.commands_loader)
        self.cli_ctx.raise_event(EVENT_INVOKER_CMD_TBL_LOADED, parser=self.parser)

        arg_check = [a for a in args if a not in
                     (CLILogging.DEBUG_FLAG, CLILogging.VERBOSE_FLAG, CLILogging.ONLY_SHOW_ERRORS_FLAG)]
        if not arg_check:
            self.cli_ctx.completion.enable_autocomplete(self.parser)
            subparser = self.parser.subparsers[tuple()]
            self.help.show_welcome(subparser)
            return CommandResultItem(None, exit_code=0)

        if args[0].lower() == 'help':
            args[0] = '--help'

        self.cli_ctx.completion.enable_autocomplete(self.parser)

        self.cli_ctx.raise_event(EVENT_INVOKER_PRE_PARSE_ARGS, args=args)
        parsed_args = self.parser.parse_args(args)
        self.cli_ctx.raise_event(EVENT_INVOKER_POST_PARSE_ARGS, command=parsed_args.command, args=parsed_args)

        self._validation(parsed_args)

        # save the command name (leaf in the tree)
        self.data['command'] = parsed_args.command
        cmd = parsed_args.func
        if hasattr(parsed_args, 'cmd'):
            parsed_args.cmd = cmd
        deprecations = getattr(parsed_args, '_argument_deprecations', [])
        if cmd.deprecate_info:
            deprecations.append(cmd.deprecate_info)

        previews = getattr(parsed_args, '_argument_previews', [])
        if cmd.preview_info:
            previews.append(cmd.preview_info)

        experimentals = getattr(parsed_args, '_argument_experimentals', [])
        if cmd.experimental_info:
            experimentals.append(cmd.experimental_info)

        params = self._filter_params(parsed_args)

        # search for implicit deprecation
        path_comps = cmd.name.split()[:-1]
        implicit_deprecate_info = None
        while path_comps and not implicit_deprecate_info:
            implicit_deprecate_info = resolve_deprecate_info(self.cli_ctx, ' '.join(path_comps))
            del path_comps[-1]

        if implicit_deprecate_info:
            deprecate_kwargs = implicit_deprecate_info.__dict__.copy()
            deprecate_kwargs['object_type'] = 'command'
            del deprecate_kwargs['_get_tag']
            del deprecate_kwargs['_get_message']
            deprecations.append(ImplicitDeprecated(cli_ctx=self.cli_ctx, **deprecate_kwargs))

        # search for implicit preview
        path_comps = cmd.name.split()[:-1]
        implicit_preview_info = None
        while path_comps and not implicit_preview_info:
            implicit_preview_info = resolve_preview_info(self.cli_ctx, ' '.join(path_comps))
            del path_comps[-1]

        if implicit_preview_info:
            preview_kwargs = implicit_preview_info.__dict__.copy()
            preview_kwargs['object_type'] = 'command'
            previews.append(ImplicitPreviewItem(cli_ctx=self.cli_ctx, **preview_kwargs))

        # search for implicit experimental
        path_comps = cmd.name.split()[:-1]
        implicit_experimental_info = None
        while path_comps and not implicit_experimental_info:
            implicit_experimental_info = resolve_experimental_info(self.cli_ctx, ' '.join(path_comps))
            del path_comps[-1]

        if implicit_experimental_info:
            experimental_kwargs = implicit_experimental_info.__dict__.copy()
            experimental_kwargs['object_type'] = 'command'
            experimentals.append(ImplicitExperimentalItem(cli_ctx=self.cli_ctx, **experimental_kwargs))

        if not self.cli_ctx.only_show_errors:
            for d in deprecations:
                print(d.message, file=sys.stderr)
            for p in previews:
                print(p.message, file=sys.stderr)
            for p in experimentals:
                print(p.message, file=sys.stderr)

        cmd_result = parsed_args.func(params)
        cmd_result = todict(cmd_result)

        event_data = {'result': cmd_result}
        self.cli_ctx.raise_event(EVENT_INVOKER_TRANSFORM_RESULT, event_data=event_data)
        self.cli_ctx.raise_event(EVENT_INVOKER_FILTER_RESULT, event_data=event_data)

        return CommandResultItem(event_data['result'],
                                 exit_code=0,
                                 table_transformer=cmd_tbl[parsed_args.command].table_transformer,
                                 is_query_active=self.data['query_active'],
                                 raw_result=cmd_result)
