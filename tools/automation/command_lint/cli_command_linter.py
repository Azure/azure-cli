import os

class Linter():
    def __init__(self, command_table=None, all_yaml_help=None, command_tree=None):
        self.command_table = command_table
        self.command_tree = command_tree
        self.all_yaml_help = all_yaml_help

        self.rules = [
            self.unrecognized_help_entry_rule,
            self.faulty_help_type_rule,
            self.missing_command_help_rule,
            self.missing_group_help_rule
        ]

    def run(self):
        print('Running Command Table Linter...')
        for callable_rule in self.rules:
            print(os.linesep)
            callable_rule()

    def unrecognized_help_entry_rule(self):
        print('Checking unrecognized commands and command-groups in help...')
        for name in self.all_yaml_help:
            if not self.command_tree.in_tree(name.split()):
                print('--Help-Entry: `%s`- Not a recognized command or command-group.' % name)

    def faulty_help_type_rule(self):
        print('Checking faulty help types for commands..')
        for name, help_entry in self.all_yaml_help.items():
            subtree, _, leftover = self.command_tree.get_sub_tree(name.split())
            help_type = help_entry['type']
            if help_type != 'group' and subtree.children and not leftover:
                print('--Command-Group: `%s`- Command-group should be help-type `group`.' % name)
            elif help_type != 'command' and name in self.command_table:
                print('--Command: `%s`- Found in command table but is not of help-type `command`.' % name)

    def missing_command_help_rule(self):
        print('Checking missing help for commands...')
        for command_name in self.command_table:
            if not self.command_table.get(command_name).description:
                print('--Command: `%s`- Missing help.' % command_name)

    def missing_group_help_rule(self):
        print('Checking missing help for command-groups...')
        command_args = []
        def _check_group_help(subtree):
            command_args.append(subtree.data)
            if subtree.children:
                group_name = ' '.join(command_args)
                if group_name not in self.all_yaml_help:
                    print('--Command-Group: `%s`- Missing help.' % group_name)
            for child_tree in subtree.children.values():
                _check_group_help(child_tree)
            command_args.pop()

        for subtree in self.command_tree.children.values():
            _check_group_help(subtree)
