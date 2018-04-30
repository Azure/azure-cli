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


@help_file_entry_rule
def unrecognized_help_parameter_rule(linter, help_entry):
    if help_entry not in linter.commands:
        return

    param_help_names = linter.get_help_entry_parameter_names(help_entry)
    violations = []
    for param_help_name in param_help_names:
        if not linter.is_valid_parameter_help_name(help_entry, param_help_name):
            violations.append(param_help_name)
    if violations:
        raise RuleError('The following parameter help names are invalid: {}'.format(' | '.join(violations)))
