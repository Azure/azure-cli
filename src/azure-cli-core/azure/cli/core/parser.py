#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import argparse

import argcomplete

import azure.cli.core._help as _help
from azure.cli.core._util import CLIError

class IncorrectUsageError(CLIError):
    '''Raised when a command is incorrectly used and the usage should be
    displayed to the user.
    '''
    pass

class CaseInsensitiveChoicesCompleter(argcomplete.completers.ChoicesCompleter): #pylint: disable=too-few-public-methods
    def __call__(self, prefix, **kwargs):
        return (c for c in self.choices if c.lower().startswith(prefix.lower()))

# Override the choices completer with one that is case insensitive
argcomplete.completers.ChoicesCompleter = CaseInsensitiveChoicesCompleter

class EmptyDefaultCompletionFinder(argcomplete.CompletionFinder):
    def __init__(self, *args, **kwargs):
        super(EmptyDefaultCompletionFinder, self).__init__(*args, default_completer=lambda _: (),
                                                           **kwargs)

def enable_autocomplete(parser):
    argcomplete.autocomplete = EmptyDefaultCompletionFinder()
    argcomplete.autocomplete(parser, validator=lambda c, p: c.lower().startswith(p.lower()))

class AzCliCommandParser(argparse.ArgumentParser):
    """ArgumentParser implementation specialized for the
    Azure CLI utility.
    """
    def __init__(self, **kwargs):
        self.subparsers = {}
        self.parents = kwargs.get('parents', [])
        self.help_file = kwargs.pop('help_file', None)
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
            command_parser = subparser.add_parser(command_verb,
                                                  description=metadata.description,
                                                  parents=self.parents, conflict_handler='error',
                                                  help_file=metadata.help)

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
                    param = group.add_argument(
                        *arg.options_list, **arg.options)
                else:
                    param = command_parser.add_argument(
                        *arg.options_list, **arg.options)
                param.completer = arg.completer

            command_parser.set_defaults(func=metadata.handler,
                                        command=command_name,
                                        _validators=argument_validators,
                                        _parser=command_parser)
        enable_autocomplete(self)

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
                grandparent_subparser = self.subparsers[tuple(path[0:length - 1])]
                new_parser = grandparent_subparser.add_parser(path[length - 1])

                # Due to http://bugs.python.org/issue9253, we have to give the subparser
                # a destination and set it to required in order to get a meaningful error
                parent_subparser = new_parser.add_subparsers(dest='subcommand')
                parent_subparser.required = True
                self.subparsers[tuple(path[0:length])] = parent_subparser
        return parent_subparser

    def validation_error(self, message):
        from azure.cli.core.telemetry import log_telemetry
        log_telemetry('validation error', log_type='trace', prog=self.prog)
        return super(AzCliCommandParser, self).error(message)

    def error(self, message):
        from azure.cli.core.telemetry import log_telemetry
        log_telemetry('parse error', message=message, prog=self.prog)
        return super(AzCliCommandParser, self).error(message)

    def format_help(self):
        from azure.cli.core.telemetry import log_telemetry
        is_group = self.is_group()
        log_telemetry('show help', prog=self.prog)
        _help.show_help(self.prog.split()[1:],
                        self._actions[-1] if is_group else self,
                        is_group)
        self.exit()

    def is_group(self):
        return getattr(self, '_subparsers', None) is not None
