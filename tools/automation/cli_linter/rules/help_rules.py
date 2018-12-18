# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..rule_decorators import help_file_entry_rule
from ..linter import RuleError
from ..util import get_cmd_param_list_from_example


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

@help_file_entry_rule
def faulty_help_example_rule(linter, help_entry):
    violations = []
    for index, example in enumerate(linter.get_help_entry_examples(help_entry)):
        if 'az '+ help_entry not in example.get('text', ''):
            violations.append(str(index))

    if violations:
        raise RuleError('The following example entry indices do not include the command: {}'.format(
            ' | '.join(violations)))

@help_file_entry_rule
def faulty_help_example_parameters_rule(linter, help_entry):
    violations = []
    valid_commands = linter._loaded_help.keys()
    for index, example in enumerate(linter.get_help_entry_examples(help_entry)):
        example_text = example.get('text','')
        cmd_params_list = get_cmd_param_list_from_example(example_text)

        for cmd_body, params in cmd_params_list:
            cmd_list = cmd_body.split()[1:] # break down command into list of words and get rid of `az`.

            while(cmd_list and " ".join(cmd_list) not in valid_commands): # trim possible positional arguments.
                cmd_list = cmd_list[:-1]

            # if no help entry match was found, this is not a valid command.
            if not cmd_list:
                violations.append("\t\t\t'{}' is not a valid command.".format(cmd_body))
                continue

            cmd = " ".join(cmd_list)

            for param in params:
                if not linter.is_valid_parameter_help_option(cmd, param):
                    violations.append("\t\t\tOption '{}' is not a valid parameter for command '{}'.".format(param, cmd))

    if violations:
        num_err = len(violations)
        violation_str = "\n".join(violations[:25])
        violation_msg = "There is a violation:\n{}.".format(violation_str) if num_err == 1 else "There are {} violations:\n{}".format(num_err, violation_str)
        raise RuleError(violation_msg)
