# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .linter import RuleError


def exclude_from_ci(func):
    func.exclude_from_ci = True
    return func


def help_file_entry_rule(starting_message):
    return _get_decorator(starting_message, 'help_file_entries', 'get_help_entry_exclusions', 'Help-Entry: `{}`')


def command_rule(starting_message):
    return _get_decorator(starting_message, 'commands', 'get_command_exclusions', 'Command: `{}`')


def command_group_rule(starting_message):
    return _get_decorator(starting_message, 'command_groups', 'get_command_group_exclusions', 'Command-Group: `{}`')


def parameter_rule(starting_message):
    def decorator(func):
        def add_to_linter(linter_manager):
            def wrapper():
                print(starting_message)
                linter = linter_manager.linter
                for command_name in linter.commands:
                    for parameter_name in linter.get_command_parameters(command_name):
                        parameter_exclusions = linter_manager.get_parameter_exclusions(command_name)
                        if parameter_name not in parameter_exclusions or \
                                func.__name__ not in parameter_exclusions.get(parameter_name):
                            try:
                                func(linter, command_name, parameter_name)
                            except RuleError as ex:
                                linter_manager.mark_rule_failure()
                                _print_violation(ex, 'Parameter: `{}` in Command: `{}`', parameter_name, command_name)
            linter_manager.add_rule('params', wrapper)
        add_to_linter.linter_rule = True
        return add_to_linter
    return decorator


def _get_decorator(starting_message, rule_group, linter_exclusion_func_name, print_format):
    def decorator(func):
        def add_to_linter(linter_manager):
            def wrapper():
                print(starting_message)
                linter = linter_manager.linter
                for iter_entity in getattr(linter, rule_group):
                    exclusions = getattr(linter_manager, linter_exclusion_func_name)()
                    if iter_entity not in exclusions or func.__name__ not in exclusions.get(iter_entity):
                        try:
                            func(linter, iter_entity)
                        except RuleError as ex:
                            linter_manager.mark_rule_failure()
                            _print_violation(ex, print_format, iter_entity)
            linter_manager.add_rule(rule_group, wrapper)
        add_to_linter.linter_rule = True
        return add_to_linter
    return decorator


def _print_violation(ex, format_string, *format_args):
    violation_string = format_string.format(*format_args)
    print('    {} - {}'.format(violation_string, ex))
