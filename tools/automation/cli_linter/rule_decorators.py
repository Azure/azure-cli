# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .linter import RuleError


def exclude_from_ci(func):
    func.exclude_from_ci = True
    return func


def help_file_entry_rule(func):
    return _get_decorator(func, 'help_file_entries', 'get_help_entry_exclusions', 'Help-Entry: `{}`')


def command_rule(func):
    return _get_decorator(func, 'commands', 'get_command_exclusions', 'Command: `{}`')


def command_group_rule(func):
    return _get_decorator(func, 'command_groups', 'get_command_group_exclusions', 'Command-Group: `{}`')


def parameter_rule(func):
    def add_to_linter(linter_manager):
        def wrapper():
            print('-Rule:', func.__name__)
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
                            yield _create_violation_msg(ex, 'Parameter: {}, `{}`',
                                                        command_name, parameter_name)
        linter_manager.add_rule('params', wrapper)
    add_to_linter.linter_rule = True
    return add_to_linter


def _get_decorator(func, rule_group, linter_exclusion_func_name, print_format):
    def add_to_linter(linter_manager):
        def wrapper():
            print(func.__name__)
            linter = linter_manager.linter
            for iter_entity in getattr(linter, rule_group):
                exclusions = getattr(linter_manager, linter_exclusion_func_name)()
                if iter_entity not in exclusions or func.__name__ not in exclusions.get(iter_entity):
                    try:
                        func(linter, iter_entity)
                    except RuleError as ex:
                        linter_manager.mark_rule_failure()
                        yield _create_violation_msg(ex, print_format, iter_entity)
        linter_manager.add_rule(rule_group, wrapper)
    add_to_linter.linter_rule = True
    return add_to_linter


def _create_violation_msg(ex, format_string, *format_args):
    violation_string = format_string.format(*format_args)
    return '    {} - {}'.format(violation_string, ex)
