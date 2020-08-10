# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from ..rule_decorators import CommandRule
from ..linter import RuleError, LinterSeverity


@CommandRule(LinterSeverity.HIGH)
def missing_command_help(linter, command_name):
    if not linter.get_command_help(command_name) and not linter.command_expired(command_name):
        raise RuleError('Missing help')


@CommandRule(LinterSeverity.HIGH)
def no_ids_for_list_commands(linter, command_name):
    if command_name.split()[-1] == 'list' and 'ids' in linter.get_command_parameters(command_name):
        raise RuleError('List commands should not expose --ids argument')


@CommandRule(LinterSeverity.HIGH)
def expired_command(linter, command_name):
    if linter.command_expired(command_name):
        raise RuleError('Deprecated command is expired and should be removed.')


@CommandRule(LinterSeverity.LOW)
def group_delete_commands_should_confirm(linter, command_name):
    # We cannot detect from cmd table etc whether a delete command deletes a collection, group or set of resources.
    # so warn users for every delete command.

    if command_name.split()[-1].lower() == "delete":
        if 'yes' not in linter.get_command_parameters(command_name):
            raise RuleError("If this command deletes a collection, or group of resources. "
                            "Please make sure to ask for confirmation.")
