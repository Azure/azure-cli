# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys

import argparse
import argcomplete

from knack.log import get_logger
from knack.parser import CLICommandParser
from knack.util import CLIError

import azure.cli.core.telemetry as telemetry


logger = get_logger(__name__)


class IncorrectUsageError(CLIError):
    '''Raised when a command is incorrectly used and the usage should be
    displayed to the user.
    '''
    pass


def enable_autocomplete(parser):
    argcomplete.autocomplete = argcomplete.CompletionFinder()
    argcomplete.autocomplete(parser, validator=lambda c, p: c.lower().startswith(p.lower()),
                             default_completer=lambda _: ())


class AzCliCommandParser(CLICommandParser):
    """ArgumentParser implementation specialized for the Azure CLI utility."""

    def __init__(self, cli_ctx=None, cli_help=None, **kwargs):
        self.command_source = kwargs.pop('_command_source', None)
        super(AzCliCommandParser, self).__init__(cli_ctx, cli_help=cli_help, **kwargs)

    def load_command_table(self, cmd_tbl):
        """Load a command table into our parser."""
        # If we haven't already added a subparser, we
        # better do it.
        if not self.subparsers:
            sp = self.add_subparsers(dest='_command_package')
            sp.required = True
            self.subparsers = {(): sp}

        for command_name, metadata in cmd_tbl.items():
            subparser = self._get_subparser(command_name.split())
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
                        param = CLICommandParser._add_argument(group, arg)
                    else:
                        param = CLICommandParser._add_argument(command_parser, arg)
                except argparse.ArgumentError as ex:
                    raise CLIError("command authoring error for '{}': '{}' {}".format(
                        command_name, ex.args[0].dest, ex.message))  # pylint: disable=no-member
                param.completer = arg.completer

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
        telemetry.set_command_details(
            command=self.prog[3:],
            extension_name=self.command_source.extension_name if self.command_source else None)
        telemetry.set_success(summary='show help')
        super(AzCliCommandParser, self).format_help()

    def _check_value(self, action, value):
        # Override to customize the error message when a argument is not among the available choices
        # converted value must be one of the choices (if specified)
        if action.choices is not None and value not in action.choices:
            msg = 'invalid choice: {}'.format(value)
            raise argparse.ArgumentError(action, msg)
