# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import sys
import difflib

import argparse
import argcomplete

from knack.deprecation import Deprecated
from knack.log import get_logger
from knack.parser import CLICommandParser
from knack.util import CLIError

import azure.cli.core.telemetry as telemetry
from azure.cli.core.extension import get_extension
from azure.cli.core.commands import ExtensionCommandSource
from azure.cli.core.commands.events import EVENT_INVOKER_ON_TAB_COMPLETION

logger = get_logger(__name__)


class IncorrectUsageError(CLIError):
    '''Raised when a command is incorrectly used and the usage should be
    displayed to the user.
    '''
    pass


class AzCompletionFinder(argcomplete.CompletionFinder):

    def _get_completions(self, comp_words, cword_prefix, cword_prequote, last_wordbreak_pos):
        external_completions = []
        self._parser.cli_ctx.raise_event(EVENT_INVOKER_ON_TAB_COMPLETION,
                                         external_completions=external_completions,
                                         parser=self._parser,
                                         comp_words=comp_words,
                                         cword_prefix=cword_prefix,
                                         cword_prequote=cword_prequote,
                                         last_wordbreak_pos=last_wordbreak_pos)

        return external_completions + super(AzCompletionFinder, self)._get_completions(comp_words,
                                                                                       cword_prefix,
                                                                                       cword_prequote,
                                                                                       last_wordbreak_pos)


class AzCliCommandParser(CLICommandParser):
    """ArgumentParser implementation specialized for the Azure CLI utility."""

    def __init__(self, cli_ctx=None, cli_help=None, **kwargs):
        self.command_source = kwargs.pop('_command_source', None)
        super(AzCliCommandParser, self).__init__(cli_ctx, cli_help=cli_help, **kwargs)

    def load_command_table(self, command_loader):
        """Load a command table into our parser."""
        # If we haven't already added a subparser, we
        # better do it.
        cmd_tbl = command_loader.command_table
        grp_tbl = command_loader.command_group_table
        if not self.subparsers:
            sp = self.add_subparsers(dest='_command_package')
            sp.required = True
            self.subparsers = {(): sp}

        for command_name, metadata in cmd_tbl.items():
            subparser = self._get_subparser(command_name.split(), grp_tbl)
            deprecate_info = metadata.deprecate_info
            if not subparser or (deprecate_info and deprecate_info.expired()):
                continue

            command_verb = command_name.split()[-1]
            # To work around http://bugs.python.org/issue9253, we artificially add any new
            # parsers we add to the "choices" section of the subparser.
            subparser.choices[command_verb] = command_verb

            # inject command_module designer's help formatter -- default is HelpFormatter
            fc = metadata.formatter_class or argparse.HelpFormatter

            command_parser = subparser.add_parser(command_verb,
                                                  description=metadata.description,
                                                  parents=self.parents,
                                                  conflict_handler='error',
                                                  help_file=metadata.help,
                                                  formatter_class=fc,
                                                  cli_help=self.cli_help,
                                                  _command_source=metadata.command_source)
            command_parser.cli_ctx = self.cli_ctx
            command_validator = metadata.validator
            argument_validators = []
            argument_groups = {}
            for _, arg in metadata.arguments.items():
                # don't add deprecated arguments to the parser
                deprecate_info = arg.type.settings.get('deprecate_info', None)
                if deprecate_info and deprecate_info.expired():
                    continue

                if arg.validator:
                    argument_validators.append(arg.validator)
                try:
                    if arg.arg_group:
                        try:
                            group = argument_groups[arg.arg_group]
                        except KeyError:
                            # group not found so create
                            group_name = '{} Arguments'.format(arg.arg_group)
                            group = command_parser.add_argument_group(arg.arg_group, group_name)
                            argument_groups[arg.arg_group] = group
                        param = AzCliCommandParser._add_argument(group, arg)
                    else:
                        param = AzCliCommandParser._add_argument(command_parser, arg)
                except argparse.ArgumentError as ex:
                    raise CLIError("command authoring error for '{}': '{}' {}".format(
                        command_name, ex.args[0].dest, ex.message))  # pylint: disable=no-member
                param.completer = arg.completer
                param.deprecate_info = arg.deprecate_info
            command_parser.set_defaults(
                func=metadata,
                command=command_name,
                _cmd=metadata,
                _command_validator=command_validator,
                _argument_validators=argument_validators,
                _parser=command_parser)

    def validation_error(self, message):
        telemetry.set_user_fault('validation error')
        return super(AzCliCommandParser, self).error(message)

    def error(self, message):
        telemetry.set_user_fault('parse error: {}'.format(message))
        args = {'prog': self.prog, 'message': message}
        logger.error('%(prog)s: error: %(message)s', args)
        self.print_usage(sys.stderr)
        self.exit(2)

    def format_help(self):
        extension_version = None
        extension_name = None
        try:
            if isinstance(self.command_source, ExtensionCommandSource):
                extension_name = self.command_source.extension_name
                extension_version = get_extension(self.command_source.extension_name).version
        except Exception:  # pylint: disable=broad-except
            pass

        telemetry.set_command_details(
            command=self.prog[3:],
            extension_name=extension_name,
            extension_version=extension_version)
        telemetry.set_success(summary='show help')
        super(AzCliCommandParser, self).format_help()

    def enable_autocomplete(self):
        argcomplete.autocomplete = AzCompletionFinder()
        argcomplete.autocomplete(self, validator=lambda c, p: c.lower().startswith(p.lower()),
                                 default_completer=lambda _: ())

    def _check_value(self, action, value):
        # Override to customize the error message when a argument is not among the available choices
        # converted value must be one of the choices (if specified)
        if action.choices is not None and value not in action.choices:
            if not self.command_source:
                # parser has no `command_source`, value is part of command itself
                error_msg = "{prog}: '{value}' is not in the '{prog}' command group. See '{prog} --help'.".format(
                    prog=self.prog, value=value)
            else:
                # `command_source` indicates command values have been parsed, value is an argument
                parameter = action.option_strings[0] if action.option_strings else action.dest
                error_msg = "{prog}: '{value}' is not a valid value for '{param}'. See '{prog} --help'.".format(
                    prog=self.prog, value=value, param=parameter)
            telemetry.set_user_fault(error_msg)
            logger.error(error_msg)
            candidates = difflib.get_close_matches(value, action.choices, cutoff=0.7)
            if candidates:
                print_args = {
                    's': 's' if len(candidates) > 1 else '',
                    'verb': 'are' if len(candidates) > 1 else 'is',
                    'value': value
                }
                suggestion_msg = "\nThe most similar choice{s} to '{value}' {verb}:\n".format(**print_args)
                suggestion_msg += '\n'.join(['\t' + candidate for candidate in candidates])
                print(suggestion_msg, file=sys.stderr)

            self.exit(2)

    @staticmethod
    def _add_argument(obj, arg):
        """ Only pass valid argparse kwargs to argparse.ArgumentParser.add_argument """
        from knack.parser import ARGPARSE_SUPPORTED_KWARGS

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
        else:
            if 'required' in argparse_options:
                del argparse_options['required']
            if 'metavar' not in argparse_options:
                argparse_options['metavar'] = '<{}>'.format(argparse_options['dest'].upper())
            return obj.add_argument(**argparse_options)
