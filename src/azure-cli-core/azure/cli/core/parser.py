# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys

import argparse
import argcomplete

import azure.cli.core.telemetry as telemetry
from azure.cli.core._pkg_util import handle_module_not_installed

from knack.help import show_help
from knack.log import get_logger
from knack.parser import CLICommandParser
from knack.util import CLIError

logger = get_logger(__name__)

ARGPARSE_SUPPORTED_KWARGS = [
    'option_strings',
    'dest',
    'nargs',
    'const',
    'default',
    'type',
    'choices',
    'help',
    'metavar',
    'required',
    'action'
]


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

    def _add_argument(self, obj, arg):
        # TODO: This logic should be part of knack, not az
        options_list = arg.options_list
        argparse_options = {name: value for name, value in arg.options.items() if name in ARGPARSE_SUPPORTED_KWARGS}
        return obj.add_argument(*options_list, **argparse_options)

    # TODO: If not for _add_argument this would not need to be overridden with 99% same implementation
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
                                                  formatter_class=fc)

            argument_validators = []
            argument_groups = {}
            for arg in metadata.arguments.values():
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
                    param = self._add_argument(group, arg)
                else:
                    param = self._add_argument(command_parser, arg)
                param.completer = arg.completer

            command_parser.set_defaults(
                func=metadata,
                command=command_name,
                _validators=argument_validators,
                _parser=command_parser)

    def _handle_command_package_error(self, err_msg):  # pylint: disable=no-self-use
        if err_msg and err_msg.startswith('argument _command_package: invalid choice:'):
            import re
            try:
                possible_module = re.search("argument _command_package: invalid choice: '(.+?)'",
                                            err_msg).group(1)
                handle_module_not_installed(possible_module)
            except AttributeError:
                # regular expression pattern match failed so unable to retrieve
                # module name
                pass
            except Exception as e:  # pylint: disable=broad-except
                logger.debug('Unable to handle module not installed: %s', str(e))

    def validation_error(self, message):
        telemetry.set_user_fault('validation error')
        return super(AzCliCommandParser, self).error(message)

    def error(self, message):
        telemetry.set_user_fault('parse error: {}'.format(message))
        self._handle_command_package_error(message)
        args = {'prog': self.prog, 'message': message}
        logger.error('%(prog)s: error: %(message)s', args)
        self.print_usage(sys.stderr)
        self.exit(2)

    def format_help(self):
        is_group = self.is_group()

        telemetry.set_command_details(command=self.prog[3:])
        telemetry.set_success(summary='show help')

        show_help(self.prog.split()[0],
                  self.prog.split()[1:],
                  self._actions[-1] if is_group else self,
                  is_group)
        self.exit()

    def _check_value(self, action, value):
        # Override to customize the error message when a argument is not among the available choices
        # converted value must be one of the choices (if specified)
        if action.choices is not None and value not in action.choices:
            msg = 'invalid choice: {}'.format(value)
            raise argparse.ArgumentError(action, msg)
