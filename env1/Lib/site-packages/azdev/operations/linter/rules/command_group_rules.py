# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from ..rule_decorators import command_group_rule
from ..linter import RuleError


@command_group_rule
def missing_group_help(linter, command_group_name):
    if not linter.get_command_group_help(command_group_name) and not linter.command_group_expired(command_group_name) \
            and command_group_name != '':
        raise RuleError('Missing help')


@command_group_rule
def expired_command_group(linter, command_group_name):
    if linter.command_group_expired(command_group_name):
        raise RuleError("Deprecated command group is expired and should be removed.")
