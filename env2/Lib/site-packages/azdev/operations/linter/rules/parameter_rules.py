# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from ..rule_decorators import parameter_rule
from ..linter import RuleError


@parameter_rule
def missing_parameter_help(linter, command_name, parameter_name):
    if not linter.get_parameter_help(command_name, parameter_name) and not linter.command_expired(command_name):
        raise RuleError('Missing help')


@parameter_rule
def expired_parameter(linter, command_name, parameter_name):
    if linter.parameter_expired(command_name, parameter_name):
        raise RuleError('Deprecated parameter is expired and should be removed.')


@parameter_rule
def expired_option(linter, command_name, parameter_name):
    expired_options = linter.option_expired(command_name, parameter_name)
    if expired_options:
        raise RuleError("Deprecated options '{}' are expired and should be removed.".format(', '.join(expired_options)))


@parameter_rule
def bad_short_option(linter, command_name, parameter_name):
    from knack.deprecation import Deprecated
    bad_options = []
    for option in linter.get_parameter_options(command_name, parameter_name):
        if isinstance(option, Deprecated):
            # we don't care if deprecated options are "bad options" since this is the
            # mechanism by which we get rid of them
            continue
        if not option.startswith('--') and len(option) != 2:
            bad_options.append(option)

    if bad_options:
        raise RuleError('Found multi-character short options: {}. Use a single character or '
                        'convert to a long-option.'.format(' | '.join(bad_options)))
