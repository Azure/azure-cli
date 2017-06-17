# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys

import argparse
import argcomplete

import azure.cli.core.telemetry as telemetry
import azure.cli.core._help as _help
from azure.cli.core.util import CLIError
from azure.cli.core._pkg_util import handle_module_not_installed

import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)


class IncorrectUsageError(CLIError):
    '''Raised when a command is incorrectly used and the usage should be
    displayed to the user.
    '''
    pass


class CaseInsensitiveChoicesCompleter(argcomplete.completers.ChoicesCompleter):  # pylint: disable=too-few-public-methods

    def __call__(self, prefix, **kwargs):
        return (c for c in self.choices if c.lower().startswith(prefix.lower()))


# Override the choices completer with one that is case insensitive
argcomplete.completers.ChoicesCompleter = CaseInsensitiveChoicesCompleter


def enable_autocomplete(parser):
    argcomplete.autocomplete = argcomplete.CompletionFinder()
    argcomplete.autocomplete(parser, validator=lambda c, p: c.lower().startswith(p.lower()),
                             default_completer=lambda _: ())


class AzCliCommandParser(argparse.ArgumentParser):
    """ArgumentParser implementation specialized for the
    Azure CLI utility.
    """

    def __init__(self, **kwargs):
        self.subparsers = {}
        self.parents = kwargs.get('parents', [])
        self.help_file = kwargs.pop('help_file', None)
        # We allow a callable for description to be passed in in order to delay-load any help
        # or description for a command. We better stash it away before handing it off for
        # "normal" argparse handling...
        self._description = kwargs.pop('description', None)
        super(AzCliCommandParser, self).__init__(**kwargs)

    def load_command_table(self, command_table):
        """Load a command table into our parser.
        """
        # If we haven't already added a subparser, we
        # better do it.
        if not self.subparsers:
            sp = self.add_subparsers(dest='_command_package')
            sp.required = True
            self.subparsers = {(): sp}

        for command_name, metadata in command_table.items():
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
                        group = command_parser.add_argument_group(
                            arg.arg_group, group_name)
                        argument_groups[arg.arg_group] = group
                    param = group.add_argument(
                        *arg.options_list, **arg.options)
                else:
                    try:
                        param = command_parser.add_argument(
                            *arg.options_list, **arg.options)
                    except argparse.ArgumentError:
                        dest = arg.options['dest']
                        if dest in ['no_wait', 'raw']:
                            pass
                        else:
                            raise
                param.completer = arg.completer

            command_parser.set_defaults(
                func=metadata,
                command=command_name,
                _validators=argument_validators,
                _parser=command_parser)

    def _get_subparser(self, path):
        """For each part of the path, walk down the tree of
        subparsers, creating new ones if one doesn't already exist.
        """
        for length in range(0, len(path)):
            parent_subparser = self.subparsers.get(tuple(path[0:length]), None)
            if not parent_subparser:
                # No subparser exists for the given subpath - create and register
                # a new subparser.
                # Since we know that we always have a root subparser (we created)
                # one when we started loading the command table, and we walk the
                # path from left to right (i.e. for "cmd subcmd1 subcmd2", we start
                # with ensuring that a subparser for cmd exists, then for subcmd1,
                # subcmd2 and so on), we know we can always back up one step and
                # add a subparser if one doesn't exist
                grandparent_subparser = self.subparsers[tuple(path[:length - 1])]
                new_parser = grandparent_subparser.add_parser(path[length - 1])

                # Due to http://bugs.python.org/issue9253, we have to give the subparser
                # a destination and set it to required in order to get a
                # meaningful error
                parent_subparser = new_parser.add_subparsers(dest='subcommand')
                parent_subparser.required = True
                self.subparsers[tuple(path[0:length])] = parent_subparser
        return parent_subparser

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

        _help.show_help(self.prog.split()[1:],
                        self._actions[-1] if is_group else self,
                        is_group)
        self.exit()

    def _check_value(self, action, value):
        # Override to customize the error message when a argument is not among the available choices
        # converted value must be one of the choices (if specified)
        if action.choices is not None and value not in action.choices:
            msg = 'invalid choice: {}'.format(value)
            raise argparse.ArgumentError(action, msg)

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
