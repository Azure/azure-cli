# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..rule_decorators import help_file_entry_rule


@help_file_entry_rule('Checking unrecognized commands and command-groups in help...')
def unrecognized_help_entry_rule(linter, help_entry):
    if help_entry not in linter.get_commands().union(linter.get_command_groups()):
        print('--Help-Entry: `%s`- Not a recognized command or command-group.' % help_entry)
        linter.mark_rule_failure()


@help_file_entry_rule('Checking help entries for faulty help types..')
def faulty_help_type_rule(linter, help_entry):
    mark = True
    if linter.get_help_entry_type(help_entry) != 'group' and help_entry in linter.get_command_groups():
        print('--Help-Entry: `%s`- Command-group should be help-type `group`.' % help_entry)
    elif linter.get_help_entry_type(help_entry) != 'command' and help_entry in linter.get_commands():
        print('--Help-Entry: `%s`- Found in command table but is not of help-type `command`.' % help_entry)
    else:
        mark = False
    if mark:
        linter.mark_rule_failure()
