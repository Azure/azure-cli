# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..rule_decorators import parameter_rule
from ..linter import RuleError


@parameter_rule
def missing_parameter_help_rule(linter, command_name, parameter_name):
    if not linter.get_parameter_help(command_name, parameter_name):
        raise RuleError('Missing help')

@parameter_rule
def bad_short_option_rule(linter, command_name, parameter_name):
    bad_options = []
    for option in linter.get_parameter_options(command_name, parameter_name):
        if not option.startswith('--') and len(option) != 2:
            bad_options.append(option)

    if bad_options:
        raise RuleError('Found multi-character short options: {}. Use a single character or '
        				'convert to a long-option.'.format(' | '.join(bad_options)))
