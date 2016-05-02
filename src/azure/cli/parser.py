import argparse
import azure.cli._help as _help

class IncorrectUsageError(Exception):
    '''Raised when a command is incorrectly used and the usage should be
    displayed to the user.
    '''
    pass

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

        for handler, metadata in command_table.items():
            subparser = self._get_subparser(metadata['name'].split())
            command_name = metadata['name'].split()[-1]
            # To work around http://bugs.python.org/issue9253, we artificially add any new
            # parsers we add to the "choices" section of the subparser.
            subparser.choices[command_name] = command_name
            command_parser = subparser.add_parser(command_name,
                                                  description=metadata.get('description'),
                                                  parents=self.parents, conflict_handler='resolve',
                                                  help_file=metadata.get('help_file'))
            for arg in metadata['arguments']:
                names = arg.get('name').split()
                command_parser.add_argument(*names, **{k:v for k, v in arg.items() if k != 'name' and not k.startswith('_')})
            command_parser.set_defaults(func=handler)

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

    def format_help(self):
        is_group = not self._defaults.get('func')
        _help.show_help(self.prog.split()[1:],
                        (self._actions[-1]
                         if is_group
                         else self),
                        is_group)
        self.exit()
