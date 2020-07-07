# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from knack.util import CLIError
from .linter import RuleError, LinterSeverity


class BaseRule(object):

    def __init__(self, severity):
        if severity not in LinterSeverity:
            raise CLIError("A {} rule has an invalid severity. Received {}; expected one of: {}"
                           .format(str(self.__class__), severity, list(LinterSeverity)))
        self.severity = severity


# help_file_entry_rule
class HelpFileEntryRule(BaseRule):

    def __call__(self, func):
        return _get_decorator(func, 'help_file_entries', 'Help-Entry: `{}`', self.severity)


# command_rule
class CommandRule(BaseRule):

    def __call__(self, func):
        return _get_decorator(func, 'commands', 'Command: `{}`', self.severity)


# command_group_rule
class CommandGroupRule(BaseRule):

    def __call__(self, func):
        return _get_decorator(func, 'command_groups', 'Command-Group: `{}`', self.severity)


# parameter_rule
class ParameterRule(BaseRule):

    def __call__(self, func):
        def add_to_linter(linter_manager):
            def wrapper():
                linter = linter_manager.linter

                for command_name in linter.commands:
                    for parameter_name in linter.get_command_parameters(command_name):
                        exclusion_parameters = linter_manager.exclusions.get(command_name, {}).get('parameters', {})
                        exclusions = exclusion_parameters.get(parameter_name, {}).get('rule_exclusions', [])
                        if func.__name__ not in exclusions:
                            try:
                                func(linter, command_name, parameter_name)
                            except RuleError as ex:
                                linter_manager.mark_rule_failure()
                                yield (_create_violation_msg(ex, 'Parameter: {}, `{}`', command_name, parameter_name),
                                       (command_name, parameter_name),
                                       func.__name__)

            linter_manager.add_rule('params', func.__name__, wrapper, self.severity)
        add_to_linter.linter_rule = True
        return add_to_linter


def _get_decorator(func, rule_group, print_format, severity):
    def add_to_linter(linter_manager):
        def wrapper():
            linter = linter_manager.linter

            for iter_entity in getattr(linter, rule_group):
                exclusions = linter_manager.exclusions.get(iter_entity, {}).get('rule_exclusions', [])
                if func.__name__ not in exclusions:
                    try:
                        func(linter, iter_entity)
                    except RuleError as ex:
                        linter_manager.mark_rule_failure()
                        yield (_create_violation_msg(ex, print_format, iter_entity), iter_entity, func.__name__)

        linter_manager.add_rule(rule_group, func.__name__, wrapper, severity)
    add_to_linter.linter_rule = True
    return add_to_linter


def _create_violation_msg(ex, format_string, *format_args):
    violation_string = format_string.format(*format_args)
    return '    {} - {}'.format(violation_string, ex)
