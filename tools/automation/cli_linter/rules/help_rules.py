# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..rule_decorators import help_file_entry_rule
from ..linter import RuleError


@help_file_entry_rule
def unrecognized_help_entry_rule(linter, help_entry):
    if help_entry not in linter.commands and help_entry not in linter.command_groups:
        raise RuleError('Not a recognized command or command-group')


@help_file_entry_rule
def faulty_help_type_rule(linter, help_entry):
    if linter.get_help_entry_type(help_entry) != 'group' and help_entry in linter.command_groups:
        raise RuleError('Command-group should be of help-type `group`')
    elif linter.get_help_entry_type(help_entry) != 'command' and help_entry in linter.commands:
        raise RuleError('Command should be of help-type `command`')
