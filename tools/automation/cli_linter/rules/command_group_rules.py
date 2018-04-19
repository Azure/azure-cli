# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..rule_decorators import command_group_rule, exclude_from_ci
from ..linter import RuleError


@exclude_from_ci
@command_group_rule
def missing_group_help_rule(linter, command_group_name):
    if not linter.get_command_group_help(command_group_name):
        raise RuleError('Missing help')
