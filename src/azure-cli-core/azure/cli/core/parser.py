# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import difflib

import argparse
import argcomplete

import azure.cli.core.telemetry as telemetry
from azure.cli.core.extension import get_extension
from azure.cli.core.commands import ExtensionCommandSource
from azure.cli.core.commands import AzCliCommandInvoker
from azure.cli.core.commands.events import EVENT_INVOKER_ON_TAB_COMPLETION
from azure.cli.core.command_recommender import CommandRecommender
from azure.cli.core.azclierror import UnrecognizedArgumentError
from azure.cli.core.azclierror import RequiredArgumentMissingError
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.azclierror import ArgumentUsageError
from azure.cli.core.azclierror import CommandNotFoundError
from azure.cli.core.azclierror import ValidationError

from knack.log import get_logger
from knack.parser import CLICommandParser
from knack.util import CLIError

logger = get_logger(__name__)

EXTENSION_REFERENCE = ("If the command is from an extension, "
                       "please make sure the corresponding extension is installed. "
                       "To learn more about extensions, please visit "
                       "'https://docs.microsoft.com/cli/azure/azure-cli-extensions-overview'")

OVERVIEW_REFERENCE = ("https://aka.ms/cli_ref")


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
        az_error = ValidationError(message)
        az_error.print_error()
        az_error.send_telemetry()
        self.exit(2)

    def error(self, message):
        # Get a recommended command from the CommandRecommender
        command_arguments = self._get_failure_recovery_arguments()
        cli_ctx = self.cli_ctx or (self.cli_help.cli_ctx if self.cli_help else None)
        recommender = CommandRecommender(*command_arguments, message, cli_ctx)
        recommender.set_help_examples(self.get_examples(self.prog))
        recommendations = recommender.provide_recommendations()

        az_error = ArgumentUsageError(message)
        if 'unrecognized arguments' in message:
            az_error = UnrecognizedArgumentError(message)
        elif 'arguments are required' in message:
            az_error = RequiredArgumentMissingError(message)
        elif 'invalid' in message:
            az_error = InvalidArgumentValueError(message)

        if '--query' in message:
            from azure.cli.core.util import QUERY_REFERENCE
            az_error.set_recommendation(QUERY_REFERENCE)
        elif recommendations:
            az_error.set_aladdin_recommendation(recommendations)
        az_error.print_error()
        az_error.send_telemetry()
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

    def get_examples(self, command):
        if not self.cli_help:
            return []
        is_group = self.is_group()
        return self.cli_help.get_examples(command,
                                          self._actions[-1] if is_group else self,
                                          is_group)

    def enable_autocomplete(self):
        argcomplete.autocomplete = AzCompletionFinder()
        argcomplete.autocomplete(self, validator=lambda c, p: c.lower().startswith(p.lower()),
                                 default_completer=lambda *args, **kwargs: ())

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
        elif action and action.dest in ('_subcommand', '_command_package'):
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

        return command, self._raw_arguments, extension

    def _get_values(self, action, arg_strings):
        value = super(AzCliCommandParser, self)._get_values(action, arg_strings)
        if action.dest and isinstance(action.dest, str) and not action.dest.startswith('_'):
            self.specified_arguments.append(action.dest)
        return value

    def parse_known_args(self, args=None, namespace=None):
        # retrieve the raw argument list in case parsing known arguments fails.
        self._raw_arguments = args
        # if parsing known arguments succeeds, get the command namespace and the argument list
        self._namespace, self._raw_arguments = super().parse_known_args(args=args, namespace=namespace)
        return self._namespace, self._raw_arguments

    def _check_value(self, action, value):  # pylint: too-many-locals, too-many-branches
        # Override to customize the error message when a argument is not among the available choices
        # converted value must be one of the choices (if specified)
        if action.choices is not None and value not in action.choices:  # pylint: disable=too-many-nested-blocks
            # self.cli_ctx is None when self.prog is beyond 'az', such as 'az iot'.
            # use cli_ctx from cli_help which is not lost.
            cli_ctx = self.cli_ctx or (self.cli_help.cli_ctx if self.cli_help else None)

            command_name_inferred = self.prog
            use_dynamic_install = 'no'
            if not self.command_source:
                from azure.cli.core.extension.dynamic_install import try_install_extension
                candidates = []
                args = self.prog.split() + self._raw_arguments
                # Check if the command is from an extension. If yes, try to fix by installing the extension, then exit.
                # The command will be rerun in another process.
                use_dynamic_install = try_install_extension(self, args)
                # parser has no `command_source`, value is part of command itself
                error_msg = "'{value}' is misspelled or not recognized by the system.".format(value=value)
                az_error = CommandNotFoundError(error_msg)
                candidates = difflib.get_close_matches(value, action.choices, cutoff=0.7)
                if candidates:
                    # use the most likely candidate to replace the misspelled command
                    args_inferred = [item if item != value else candidates[0] for item in args]
                    command_name_inferred = ' '.join(args_inferred).split('-')[0]
            else:
                # `command_source` indicates command values have been parsed, value is an argument
                parameter = action.option_strings[0] if action.option_strings else action.dest
                error_msg = "{prog}: '{value}' is not a valid value for '{param}'. Allowed values: {choices}.".format(
                    prog=self.prog, value=value, param=parameter, choices=', '.join([str(x) for x in action.choices]))
                az_error = InvalidArgumentValueError(error_msg)
                candidates = difflib.get_close_matches(value, action.choices, cutoff=0.7)

            command_arguments = self._get_failure_recovery_arguments(action)
            if candidates:
                az_error.set_recommendation("Did you mean '{}' ?".format(candidates[0]))

            # recommend a command for user
            recommender = CommandRecommender(*command_arguments, error_msg, cli_ctx)
            recommender.set_help_examples(self.get_examples(command_name_inferred))
            recommendations = recommender.provide_recommendations()
            if recommendations:
                az_error.set_aladdin_recommendation(recommendations)

            # remind user to check extensions if we can not find a command to recommend
            if isinstance(az_error, CommandNotFoundError) \
                    and not az_error.recommendations and self.prog == 'az' \
                    and use_dynamic_install == 'no':
                az_error.set_recommendation(EXTENSION_REFERENCE)

            az_error.print_error()
            az_error.send_telemetry()

            self.exit(2)
