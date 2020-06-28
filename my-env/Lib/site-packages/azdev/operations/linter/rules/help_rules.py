# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import shlex

import re
import mock

from knack.log import get_logger

from ..rule_decorators import HelpFileEntryRule
from ..linter import RuleError, LinterSeverity
from ..util import LinterError

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=no-value-for-parameter


# 'az' space then repeating runs of quoted tokens or non quoted characters
_az_pattern = 'az\s*' + '(([^\"\'])*|' + '((\"[^\"]*\"\s*)|(\'[^\']*\'\s*))' + ')'  # noqa: W605
# match the two types of command substitutions
_CMD_SUB_1 = re.compile("\$\(\s*" + "(" + _az_pattern + ")" + "\)")  # noqa: W605
_CMD_SUB_2 = re.compile("`\s*" + "(" + _az_pattern + ")" + "`")  # noqa: W605

logger = get_logger(__name__)


@HelpFileEntryRule(LinterSeverity.HIGH)
def unrecognized_help_entry_rule(linter, help_entry):
    if help_entry not in linter.commands and help_entry not in linter.command_groups:
        raise RuleError('Not a recognized command or command-group')


@HelpFileEntryRule(LinterSeverity.HIGH)
def faulty_help_type_rule(linter, help_entry):
    if linter.get_help_entry_type(help_entry) != 'group' and help_entry in linter.command_groups:
        raise RuleError('Command-group should be of help-type `group`')
    if linter.get_help_entry_type(help_entry) != 'command' and help_entry in linter.commands:
        raise RuleError('Command should be of help-type `command`')


@HelpFileEntryRule(LinterSeverity.HIGH)
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


@HelpFileEntryRule(LinterSeverity.HIGH)
def faulty_help_example_rule(linter, help_entry):
    violations = []
    for index, example in enumerate(linter.get_help_entry_examples(help_entry)):
        if 'az ' + help_entry not in example.get('text', ''):
            violations.append(str(index))

    if violations:
        raise RuleError('The following example entry indices do not include the command: {}'.format(
            ' | '.join(violations)))


@HelpFileEntryRule(LinterSeverity.HIGH)
def faulty_help_example_parameters_rule(linter, help_entry):
    parser = linter.command_parser
    violations = []

    for example in linter.get_help_entry_examples(help_entry):
        supported_profiles = example.get('supported-profiles')
        if supported_profiles and 'latest' not in supported_profiles:
            logger.warning("\n\tSKIPPING example: %s\n\tas 'latest' is not in its supported profiles."
                           "\n\t\tsupported-profiles: %s.", example['text'], example['supported-profiles'])
            continue

        unsupported_profiles = example.get('unsupported-profiles')
        if unsupported_profiles and 'latest' in unsupported_profiles:
            logger.warning("\n\tSKIPPING example: %s\n\tas 'latest' is in its unsupported profiles."
                           "\n\t\tunsupported-profiles: %s.", example['text'], example['unsupported-profiles'])
            continue

        example_text = example.get('text', '')
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


# Faulty help example parameters rule helpers

@mock.patch("azure.cli.core.parser.AzCliCommandParser._check_value")
@mock.patch("argparse.ArgumentParser._get_value")
@mock.patch("azure.cli.core.parser.AzCliCommandParser.error")
def _lint_example_command(command, parser, mocked_error_method, mocked_get_value, mocked_check_value):  # pylint: disable=unused-argument
    def get_value_side_effect(action, arg_string):  # pylint: disable=unused-argument
        return arg_string
    mocked_error_method.side_effect = LinterError  # mock call of parser.error so usage won't be printed.
    mocked_get_value.side_effect = get_value_side_effect

    violation = None
    nested_commands = []

    try:
        command_args = shlex.split(command, comments=True)[1:]  # split commands into command args, ignore comments.
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
    # handle single and double quotes properly
    lines = example_text.splitlines()
    example_text = ""
    quote = None
    for line in lines:
        for ch in line:
            if quote is None:
                if ch in ('"', "'"):
                    quote = ch
            elif ch == quote:
                quote = None
        if quote is None and line.endswith("\\"):
            # attach this line with removed '\' and no '\n' (space at the end to keep consistent with initial algorithm)
            example_text += line[0:-1] + " "
        elif quote is not None:
            # attach this line without '\n'
            example_text += line
        else:
            # attach this line with '\n' as no quote and no continuation
            example_text += line + "\n"
    # this is also for consistency with original algorithm
    example_text = example_text.replace("\\ ", " ")

    commands = example_text.splitlines()
    processed_commands = []
    for command in commands:  # filter out commands
        command.strip()
        if command.startswith("az"):  # if this is a single az command add it.
            processed_commands.append(command)

        for re_prog in [_CMD_SUB_1, _CMD_SUB_2]:
            start = 0
            match = re_prog.search(command, start)
            while match:  # while there is a nested az command of type 1 $( az ...)
                processed_commands.append(match.group(1).strip())  # add it
                start = match.end(1)  # get index of rest of string
                match = re_prog.search(command, start)  # attempt to get next match

    return processed_commands


def _process_command_args(command_args):
    result_args = []
    new_commands = []
    operators = ["&&", "||", "|"]

    for arg in command_args:  # strip unnecessary punctuation, otherwise arg validation could fail.
        if arg in operators:  # handle cases where multiple commands are connected by control operators or pipe.
            idx = command_args.index(arg)
            maybe_new_command = " ".join(command_args[idx:])

            idx = maybe_new_command.find("az ")
            if idx != -1:
                new_commands.append(maybe_new_command[idx:])  # remaining command is in fact a new command / commands.
            break

        result_args.append(arg)

    return result_args, new_commands
