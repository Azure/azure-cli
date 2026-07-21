# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse

from .deprecation import Deprecated
from .events import EVENT_PARSER_GLOBAL_CREATE
from .log import get_logger
from .util import CtxTypeError

logger = get_logger(__name__)

# List of keyword arguments supported in argparse
# from https://github.com/python/cpython/blob/master/Lib/argparse.py#L748
ARGPARSE_SUPPORTED_KWARGS = [
    'option_strings',
    'dest',
    'nargs',
    'const',
    'default',
    'type',
    'choices',
    'required',
    'help',
    'metavar',
    'action',
    'default_value_source'
]


class CLICommandParser(argparse.ArgumentParser):

    @staticmethod
    def create_global_parser(cli_ctx=None):
        global_parser = argparse.ArgumentParser(prog=cli_ctx.name, add_help=False)
        arg_group = global_parser.add_argument_group('global', 'Global Arguments')
        cli_ctx.raise_event(EVENT_PARSER_GLOBAL_CREATE, arg_group=arg_group)
        return global_parser

    @staticmethod
    def _add_argument(obj, arg):
        """ Only pass valid argparse kwargs to argparse.ArgumentParser.add_argument """
        argparse_options = {name: value for name, value in arg.options.items() if name in ARGPARSE_SUPPORTED_KWARGS}
        if arg.options_list:
            scrubbed_options_list = []
            for item in arg.options_list:

                if isinstance(item, Deprecated):
                    # don't add expired options to the parser
                    if item.expired():
                        continue

                    class _DeprecatedOption(str):
                        def __new__(cls, *args, **kwargs):
                            instance = str.__new__(cls, *args, **kwargs)
                            return instance

                    option = _DeprecatedOption(item.target)
                    setattr(option, 'deprecate_info', item)
                    item = option
                scrubbed_options_list.append(item)
            return obj.add_argument(*scrubbed_options_list, **argparse_options)

        if 'required' in argparse_options:
            del argparse_options['required']
        if 'metavar' not in argparse_options:
            argparse_options['metavar'] = '<{}>'.format(argparse_options['dest'].upper())
        return obj.add_argument(**argparse_options)

    @staticmethod
    def _expand_prefixed_files(args):
        """ Load arguments prefixed with '@' from file as string

        :param args: Arguments passed from command line
        :type args: list
        """
        for arg, _ in enumerate(args):
            if args[arg].startswith('@'):
                try:
                    logger.debug('Attempting to read file %s', args[arg][1:])
                    # Use the default system encoding: https://docs.python.org/3/library/functions.html#open
                    with open(args[arg][1:], 'r') as f:  # pylint: disable=unspecified-encoding
                        content = f.read()
                    args[arg] = content
                except IOError:
                    # Leave arg unmodified
                    logger.debug('File Error: Failed to open %s, assume not a file', args[arg][1:])
        return args

    def __init__(self, cli_ctx=None, cli_help=None, **kwargs):
        """ Create the argument parser

        :param cli_ctx: CLI Context
        :type cli_ctx: knack.cli.CLI
        :param kwargs: These kwargs are typically used by argparse when creating the subparsers
        """
        from .cli import CLI
        if cli_ctx is not None and not isinstance(cli_ctx, CLI):
            raise CtxTypeError(cli_ctx)
        self.cli_ctx = cli_ctx
        self.cli_help = cli_help
        self.subparsers = {}
        self.parents = kwargs.get('parents', [])
        self.help_file = kwargs.pop('help_file', None)
        # We allow a callable for description to be passed in in order to delay-load any help
        # or description for a command. We better stash it away before handing it off for
        # "normal" argparse handling...
        self._description = kwargs.pop('description', None)
        super().__init__(**kwargs)

    def load_command_table(self, command_loader):
        """ Process the command table and load it into the parser

        :param cmd_tbl: A dictionary containing the commands
        :type cmd_tbl: dict
        """
        cmd_tbl = command_loader.command_table
        grp_tbl = command_loader.command_group_table
        if not cmd_tbl:
            raise ValueError('The command table is empty. At least one command is required.')
        # If we haven't already added a subparser, we
        # better do it.
        if not self.subparsers:
            sp = self.add_subparsers(dest='_command')
            sp.required = True
            self.subparsers = {(): sp}

        for command_name, metadata in cmd_tbl.items():
            subparser = self._get_subparser(command_name.split(), grp_tbl)
            command_verb = command_name.split()[-1]
            # To work around http://bugs.python.org/issue9253, we artificially add any new
            # parsers we add to the "choices" section of the subparser.
            subparser = self._get_subparser(command_name.split(), grp_tbl)
            deprecate_info = metadata.deprecate_info
            if not subparser or (deprecate_info and deprecate_info.expired()):
                continue
            # inject command_module designer's help formatter -- default is HelpFormatter
            fc = metadata.formatter_class or argparse.HelpFormatter

            command_parser = subparser.add_parser(command_verb,
                                                  description=metadata.description,
                                                  parents=self.parents,
                                                  conflict_handler='error',
                                                  help_file=metadata.help,
                                                  formatter_class=fc,
                                                  cli_help=self.cli_help)
            command_parser.cli_ctx = self.cli_ctx
            command_validator = metadata.validator
            argument_validators = []
            argument_groups = {}
            for arg in metadata.arguments.values():

                # don't add deprecated arguments to the parser
                deprecate_info = arg.type.settings.get('deprecate_info', None)
                if deprecate_info and deprecate_info.expired():
                    continue

                if arg.validator:
                    argument_validators.append(arg.validator)
                if arg.arg_group:
                    try:
                        group = argument_groups[arg.arg_group]
                    except KeyError:
                        # group not found so create
                        group_name = '{} Arguments'.format(arg.arg_group)
                        group = command_parser.add_argument_group(arg.arg_group, group_name)
                        argument_groups[arg.arg_group] = group
                    param = CLICommandParser._add_argument(group, arg)
                else:
                    param = CLICommandParser._add_argument(command_parser, arg)
                param.completer = arg.completer
                param.deprecate_info = arg.deprecate_info
                param.preview_info = arg.preview_info
                param.experimental_info = arg.experimental_info
                param.default_value_source = arg.default_value_source
            command_parser.set_defaults(
                func=metadata,
                command=command_name,
                _command_validator=command_validator,
                _argument_validators=argument_validators,
                _parser=command_parser)

    def _get_subparser(self, path, group_table=None):
        """For each part of the path, walk down the tree of
        subparsers, creating new ones if one doesn't already exist.
        """
        group_table = group_table or {}
        for length in range(0, len(path)):
            parent_path = path[:length]
            parent_subparser = self.subparsers.get(tuple(parent_path), None)
            if not parent_subparser:
                # No subparser exists for the given subpath - create and register
                # a new subparser.
                # Since we know that we always have a root subparser (we created)
                # one when we started loading the command table, and we walk the
                # path from left to right (i.e. for "cmd subcmd1 subcmd2", we start
                # with ensuring that a subparser for cmd exists, then for subcmd1,
                # subcmd2 and so on), we know we can always back up one step and
                # add a subparser if one doesn't exist
                command_group = group_table.get(' '.join(parent_path))
                if command_group:
                    deprecate_info = command_group.group_kwargs.get('deprecate_info', None)
                    if deprecate_info and deprecate_info.expired():
                        continue
                grandparent_path = path[:length - 1]
                grandparent_subparser = self.subparsers[tuple(grandparent_path)]
                new_path = path[length - 1]
                new_parser = grandparent_subparser.add_parser(new_path, cli_help=self.cli_help)

                # Due to http://bugs.python.org/issue9253, we have to give the subparser
                # a destination and set it to required in order to get a meaningful error
                parent_subparser = new_parser.add_subparsers(dest='_subcommand')
                command_group = group_table.get(' '.join(parent_path), None)
                deprecate_info = None
                if command_group:
                    deprecate_info = command_group.group_kwargs.get('deprecate_info', None)
                parent_subparser.required = True
                parent_subparser.deprecate_info = deprecate_info
                self.subparsers[tuple(path[0:length])] = parent_subparser
        return parent_subparser

    def validation_error(self, message):
        return super().error(message)

    def is_group(self):
        """ Determine if this parser instance represents a group
            or a command. Anything that has a func default is considered
            a group. This includes any dummy commands served up by the
            "filter out irrelevant commands based on argv" command filter """
        cmd = self._defaults.get('func', None)
        return not (cmd and cmd.handler)

    def __getattribute__(self, name):
        """ Since getting the description can be expensive (require module loads), we defer
            this until someone actually wants to use it (i.e. show help for the command)
        """
        if name == 'description':
            if self._description:
                self.description = self._description() \
                    if callable(self._description) else self._description
                self._description = None
        return object.__getattribute__(self, name)

    def format_help(self):
        is_group = self.is_group()
        self.cli_help.show_help(self.prog.split()[0],
                                self.prog.split()[1:],
                                self._actions[-1] if is_group else self,
                                is_group)
        self.exit()

    def parse_args(self, args=None, namespace=None):
        """ Overrides argparse.ArgumentParser.parse_args

        Enables '@'-prefixed files to be expanded before arguments are processed
        by ArgumentParser.parse_args as usual
        """
        self._expand_prefixed_files(args)
        return super().parse_args(args)

    def _check_value(self, action, value):
        # Override to customize the error message when a argument is not among the available choices
        # converted value must be one of the choices (if specified)
        import difflib
        import sys

        if action.choices is not None and value not in action.choices:
            if action.dest in ["_command", "_subcommand"]:
                # Command
                error_msg = "{prog}: '{value}' is not in the '{prog}' command group. See '{prog} --help'.".format(
                    prog=self.prog, value=value)
                logger.error(error_msg)
                # Show suggestions
                candidates = difflib.get_close_matches(value, action.choices, cutoff=0.7)
                if candidates:
                    suggestion_msg = "\nThe most similar choices to '{value}':\n".format(value=value)
                    suggestion_msg += '\n'.join(['\t' + candidate for candidate in candidates])
                    print(suggestion_msg, file=sys.stderr)
            else:
                # Argument
                error_msg = "{prog}: '{value}' is not a valid value for '{name}'.".format(
                    prog=self.prog, value=value,
                    name=argparse._get_action_name(action))  # pylint: disable=protected-access
                logger.error(error_msg)
                # Show all allowed values
                suggestion_msg = "Allowed values: " + ', '.join(action.choices)
                print(suggestion_msg, file=sys.stderr)
            self.exit(2)
