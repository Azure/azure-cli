import os

class Linter():
    def __init__(self, command_table=None, all_yaml_help=None):
        self.command_table = command_table
        self.all_yaml_help = all_yaml_help

        self.rules = [
            self.faulty_command_type_rule,
            self.unrecognized_command_rule,
            self.missing_help_rule,
        ]

    def run(self):
        print('Running Command Table Linter...')
        for callable_rule in self.rules:
            print(os.linesep)
            callable_rule()


    def faulty_command_type_rule(self):
        print('Checking faulty help types for commands..')
        for name, help_entry in self.all_yaml_help.items():
            if help_entry['type'] != 'command' and name in self.command_table:
                print('--Command: `%s`- Found in command table but is not of type `command`.' % name)

    def unrecognized_command_rule(self):
        print('Checking unrecognized commands in help...')
        for name, help_entry in self.all_yaml_help.items():
            if help_entry['type'] == 'command' and name not in self.command_table:
                print('--Command: `%s`- Not found in command table.' % name)

    def missing_help_rule(self):
        print('Checking missing help for commands...')
        for command_name in self.command_table:
            if not self.command_table.get(command_name).description:
                print('--Command: `%s`- Missing help.' % command_name)

