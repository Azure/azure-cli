# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from ..rule_decorators import CommandGroupRule
from ..linter import RuleError, LinterSeverity


@CommandGroupRule(LinterSeverity.HIGH)
def missing_group_help(linter, command_group_name):
    if not linter.get_command_group_help(command_group_name) and not linter.command_group_expired(command_group_name) \
            and command_group_name != '':
        raise RuleError('Missing help')


@CommandGroupRule(LinterSeverity.HIGH)
def expired_command_group(linter, command_group_name):
    if linter.command_group_expired(command_group_name):
        raise RuleError("Deprecated command group is expired and should be removed.")


@CommandGroupRule(LinterSeverity.MEDIUM)
def require_wait_command_if_no_wait(linter, command_group_name):
    # If any command within a command group or subgroup exposes the --no-wait parameter,
    # the wait command should be exposed.

    # find commands under this group. A command in this group has one more token than the group name.
    group_command_names = [cmd for cmd in linter.commands if cmd.startswith(command_group_name) and
                           len(cmd.split()) == len(command_group_name.split()) + 1]

    # if one of the commands in this group ends with wait we are good
    for cmd in group_command_names:
        cmds = cmd.split()
        if cmds[-1].lower() == "wait":
            return

    # otherwise there is no wait command. If a command in this group has --no-wait, then error out.
    for cmd in group_command_names:
        if linter.get_command_metadata(cmd).supports_no_wait:
            raise RuleError("Group does not have a 'wait' command, yet '{}' exposes '--no-wait'".format(cmd))
