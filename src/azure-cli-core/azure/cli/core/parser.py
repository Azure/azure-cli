# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import sys
import difflib

import argparse
import argcomplete

import azure.cli.core.telemetry as telemetry
from azure.cli.core.azlogging import CommandLoggerContext
from azure.cli.core.extension import get_extension
from azure.cli.core.commands import ExtensionCommandSource
from azure.cli.core.commands import AzCliCommandInvoker
from azure.cli.core.commands.events import EVENT_INVOKER_ON_TAB_COMPLETION

from knack.log import get_logger
from knack.parser import CLICommandParser
from knack.util import CLIError

logger = get_logger(__name__)


class IncorrectUsageError(CLIError):
    '''Raised when a command is incorrectly used and the usage should be
    displayed to the user.
    '''
    pass  # pylint: disable=unnecessary-pass


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

    @staticmethod
    def recommendation_provider(version, command, parameters, extension):  # pylint: disable=unused-argument
        logger.debug("recommendation_provider: version: %s, command: %s, parameters: %s, extension: %s",
                     version, command, parameters, extension)
        return []

    def __init__(self, cli_ctx=None, cli_help=None, **kwargs):
        self.command_source = kwargs.pop('_command_source', None)
        self._raw_arguments = None
        self._namespace = None
        self._suggestion_msg = []
        self.subparser_map = {}
        self.specified_arguments = []
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
            self.subparser_map[command_name] = command_parser
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
                param.preview_info = arg.preview_info
                param.experimental_info = arg.experimental_info
                param.default_value_source = arg.default_value_source
            command_parser.set_defaults(
                func=metadata,
                command=command_name,
                _cmd=metadata,
                _command_validator=command_validator,
                _argument_validators=argument_validators,
                _parser=command_parser)

    def validation_error(self, message):
        telemetry.set_user_fault('validation error: {}'.format(message))
        return super(AzCliCommandParser, self).error(message)

    def error(self, message):
        telemetry.set_user_fault('parse error: {}'.format(message))
        args = {'prog': self.prog, 'message': message}
        with CommandLoggerContext(logger):
            logger.error('%(prog)s: error: %(message)s', args)
        self.print_usage(sys.stderr)
        failure_recovery_recommendations = self._get_failure_recovery_recommendations()
        self._suggestion_msg.extend(failure_recovery_recommendations)
        self._print_suggestion_msg(sys.stderr)
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

    def _get_failure_recovery_arguments(self, action=None):
        # Strip the leading "az " and any extraneous whitespace.
        command = self.prog[3:].strip()
        parameters = []
        parameter_set = set()
        raw_arguments = None
        extension = None

        # Extract only parameter names to ensure GPDR compliance
        def extract_safe_params(parameters):
            return AzCliCommandInvoker._extract_parameter_names(parameters)  # pylint: disable=protected-access

        # Check for extension name attribute
        def has_extension_name(command_source):
            is_extension_command_source = isinstance(command_source, ExtensionCommandSource)
            has_extension_name = False

            if is_extension_command_source:
                has_extension_name = hasattr(command_source, 'extension_name')

            return is_extension_command_source and has_extension_name

        # If the arguments have been processed into a namespace...
        if self._namespace:
            # Select the parsed command.
            if hasattr(self._namespace, 'command'):
                command = self._namespace.command
        # Parse parameter names from user input.
        if self._raw_arguments:
            raw_arguments = self._raw_arguments
            parameters = extract_safe_params(self._raw_arguments)

        for parameter in parameters:
            parameter_set.add(parameter)

        # If we can retrieve the extension from the current parser's command source...
        if has_extension_name(self.command_source):
            extension = self.command_source.extension_name
        # Otherwise, the command may have not been in a command group. The command source will not be
        # set in this case.
        elif action and action.dest == '_subcommand':
            # Get all parsers in the set of possible actions.
            parsers = list(action.choices.values())
            parser = parsers[0] if parsers else None
            # If the first parser comes from an extension...
            if parser and has_extension_name(parser.command_source):
                # We're looking for a subcommand under an extension command group. Set the
                # extension to reflect this.
                extension = parser.command_source.extension_name
            # Extend the command if the first raw argument is not a parameter.
            if raw_arguments and raw_arguments[0] not in parameter_set:
                command = '{cmd} {arg}'.format(cmd=command, arg=raw_arguments[0])
        # Otherwise, only set the extension if every subparser comes from an extension. This occurs
        # when an unrecognized argument is passed to a command from an extension.
        elif isinstance(self.subparser_map, dict):
            for _, subparser in self.subparser_map.items():
                if isinstance(subparser.command_source, ExtensionCommandSource):
                    extension = subparser.command_source.extension_name
                else:
                    extension = None
                    break

        return command, parameters, extension

    def _get_failure_recovery_recommendations(self, action=None, **kwargs):
        # Gets failure recovery recommendations
        from azure.cli.core import __version__ as core_version
        failure_recovery_arguments = self._get_failure_recovery_arguments(action)
        recommendations = AzCliCommandParser.recommendation_provider(core_version,
                                                                     *failure_recovery_arguments,
                                                                     **kwargs)
        return recommendations

    def _get_values(self, action, arg_strings):
        value = super(AzCliCommandParser, self)._get_values(action, arg_strings)
        if action.dest and isinstance(action.dest, str) and not action.dest.startswith('_'):
            self.specified_arguments.append(action.dest)
        return value

    def _print_suggestion_msg(self, file=None):
        if self._suggestion_msg:
            print('\n'.join(self._suggestion_msg), file=file)

    def parse_known_args(self, args=None, namespace=None):
        # retrieve the raw argument list in case parsing known arguments fails.
        self._raw_arguments = args
        # if parsing known arguments succeeds, get the command namespace and the argument list
        self._namespace, self._raw_arguments = super().parse_known_args(args=args, namespace=namespace)
        return self._namespace, self._raw_arguments

    def _check_value(self, action, value):
        # Override to customize the error message when a argument is not among the available choices
        # converted value must be one of the choices (if specified)
        if action.choices is not None and value not in action.choices:
            if not self.command_source:
                # parser has no `command_source`, value is part of command itself
                extensions_link = 'https://docs.microsoft.com/en-us/cli/azure/azure-cli-extensions-overview'
                error_msg = ("{prog}: '{value}' is not in the '{prog}' command group. See '{prog} --help'. "
                             "If the command is from an extension, "
                             "please make sure the corresponding extension is installed. "
                             "To learn more about extensions, please visit "
                             "{extensions_link}").format(prog=self.prog, value=value, extensions_link=extensions_link)
            else:
                # `command_source` indicates command values have been parsed, value is an argument
                parameter = action.option_strings[0] if action.option_strings else action.dest
                error_msg = "{prog}: '{value}' is not a valid value for '{param}'. See '{prog} --help'.".format(
                    prog=self.prog, value=value, param=parameter)
            telemetry.set_user_fault(error_msg)
            with CommandLoggerContext(logger):
                logger.error(error_msg)
            candidates = difflib.get_close_matches(value, action.choices, cutoff=0.7)
            if candidates:
                print_args = {
                    's': 's' if len(candidates) > 1 else '',
                    'verb': 'are' if len(candidates) > 1 else 'is',
                    'value': value
                }
                self._suggestion_msg.append("\nThe most similar choice{s} to '{value}' {verb}:".format(**print_args))
                self._suggestion_msg.append('\n'.join(['\t' + candidate for candidate in candidates]))

            failure_recovery_recommendations = self._get_failure_recovery_recommendations(action)
            self._suggestion_msg.extend(failure_recovery_recommendations)
            self._print_suggestion_msg(sys.stderr)
            self.exit(2)
