# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..rule_decorators import help_file_entry_rule
from ..linter import RuleError


@help_file_entry_rule('Checking unrecognized commands and command-groups in help...')
def unrecognized_help_entry_rule(linter, help_entry):
    if help_entry not in linter.commands and help_entry not in linter.command_groups:
        raise RuleError('Not a recognized command or command-group')
        # print('--Help-Entry: `%s`- Not a recognized command or command-group.' % help_entry)
        # linter.mark_rule_failure()


@help_file_entry_rule('Checking help entries for faulty help types..')
def faulty_help_type_rule(linter, help_entry):
    if linter.get_help_entry_type(help_entry) != 'group' and help_entry in linter.command_groups:
        raise RuleError('Command-group should be of help-type `group`')
        # print('--Help-Entry: `%s`- Command-group should be help-type `group`.' % help_entry)
        # linter.mark_rule_failure()
    elif linter.get_help_entry_type(help_entry) != 'command' and help_entry in linter.commands:
        raise RuleError('Command should be of help-type `command`')
        # print('--Help-Entry: `%s`- Found in command table but is not of help-type `command`.' % help_entry)
        # linter.mark_rule_failure()
