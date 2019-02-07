# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..rule_decorators import help_file_entry_rule
from ..linter import RuleError
from ..util import LinterError
import shlex
import mock
from knack.log import get_logger
logger = get_logger(__name__)

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
    parser = linter.command_parser
    violations = []

    for example in linter.get_help_entry_examples(help_entry):
        max_profile = example.get('max_profile')
        if max_profile and max_profile != 'latest':
            logger.warning("\n\tSKIPPING example: {}\n\tas its max profile is {}, instead of latest.".format(example['text'], example['max_profile']))
            continue

        example_text = example.get('text','')
        commands = _extract_commands_from_example(example_text)
        while commands:
            command = commands.pop()
            violation, nested_commands = _lint_example_command(command, parser)

            commands.extend(nested_commands)  # append commands that are the source of any arguments
            if violation:
                violations.append(violation)

    if violations:
        num_err = len(violations)
        violation_str = "\n\n".join(violations)
        violation_msg = "\n\tThere is a violation:\n{}.".format(violation_str) if num_err == 1 else \
            "\n\tThere are {} violations:\n{}".format(num_err, violation_str)
        raise RuleError(violation_msg + "\n\n")


### Faulty help example parameters rule helpers

@mock.patch("azure.cli.core.parser.AzCliCommandParser._check_value")
@mock.patch("argparse.ArgumentParser._get_value")
@mock.patch("azure.cli.core.parser.AzCliCommandParser.error")
def _lint_example_command(command, parser, mocked_error_method, mocked_get_value, mocked_check_value):
    def get_value_side_effect(action, arg_string):
        return arg_string
    mocked_error_method.side_effect = LinterError  # mock call of parser.error so usage won't be printed.
    mocked_get_value.side_effect = get_value_side_effect

    violation = None
    nested_commands = []

    try:
        command_args = shlex.split(command)[1:]
        command_args, nested_commands = _process_command_args(command_args)
        parser.parse_args(command_args)
    except ValueError as e:  # handle exception thrown by shlex.
        if str(e) == "No closing quotation":
            violation = '\t"{}"\n\thas no closing quotation. Tip: to continue an example ' \
                        'command on the next line, use a "\\" followed by a newline.\n\t' \
                        'If needed, you can escape the "\\", like so "\\\\"'.format(command)
        else:
            raise e
    except LinterError:  # handle parsing failure due to invalid option
        violation = '\t"{}" is not a valid command'.format(command)
        if mocked_error_method.called:
            call_args = mocked_error_method.call_args
            violation = "{}.\n\t{}".format(violation, call_args[0][0])

    return violation, nested_commands

# return list of commands in the example text
def _extract_commands_from_example(example_text):

    # fold commands spanning multiple lines into one line. Split commands that use pipes
    example_text = example_text.replace("\\\n", " ")
    example_text = example_text.replace("\\ ", " ")
    example_text = example_text.replace(" | ", "\n")

    commands = example_text.splitlines()
    processed_commands = []
    for command in commands:  # filter out commands
        if command.startswith("az"):
            processed_commands.append(command)
        elif "az " in command:  # some commands start with "$(az ..." and even "`az in one case"
            idx = command.find("az ")
            command = command[idx:]
            processed_commands.append(command)

    return processed_commands


def _process_command_args(command_args):
    result_args = []
    new_commands = []
    unwanted_chars = "$()`"
    control_operators = ["&&","||"]

    for arg in command_args: # strip unnecessary punctuation, otherwise arg validation could fail.
        if arg in control_operators: # handle cases where multiple commands are connected by control operators.
            idx = command_args.index(arg)
            maybe_new_command = " ".join(command_args[idx:])

            idx = maybe_new_command.find("az ")
            if idx != -1:
                new_commands.append(maybe_new_command[idx:])  # remaining command is in fact a new command / commands.
            break

        arg = arg.strip(unwanted_chars)
        if arg.startswith("az "):  # store any new commands
            new_commands.append(arg)
        result_args.append(arg)

    return result_args, new_commands
