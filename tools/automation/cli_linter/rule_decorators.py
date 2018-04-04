# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def help_file_entry_rule(starting_message):
    return _get_decorator(starting_message, 'get_help_file_entries', 'get_help_entry_exclusions', 'help_file_entries')


def command_rule(starting_message):
    return _get_decorator(starting_message, 'get_commands', 'get_command_exclusions', 'commands')


def command_group_rule(starting_message):
    return _get_decorator(starting_message, 'get_command_groups', 'get_command_group_exclusions', 'command_groups')


def parameter_rule(starting_message):
    def decorator(func):
        def add_to_linter(linter):
            def wrapper():
                print(starting_message)
                for command_name in linter.get_commands():
                    for parameter_name in linter.get_command_parameters(command_name):
                        parameter_exclusions = linter.get_parameter_exclusions(command_name)
                        if parameter_name not in parameter_exclusions or \
                                func.__name__ not in parameter_exclusions.get(parameter_name):
                            func(linter, command_name, parameter_name)
            linter.add_rule('params', wrapper)
        add_to_linter.linter_rule = True
        return add_to_linter
    return decorator


def _get_decorator(starting_message, linter_func_name, linter_exclusion_func_name, rule_group):
    def decorator(func):
        def add_to_linter(linter):
            def wrapper():
                print(starting_message)
                for iter_entity in getattr(linter, linter_func_name)():
                    exclusions = getattr(linter, linter_exclusion_func_name)()
                    if iter_entity not in exclusions or func.__name__ not in exclusions.get(iter_entity):
                        func(linter, iter_entity)
            linter.add_rule(rule_group, wrapper)
        add_to_linter.linter_rule = True
        return add_to_linter
    return decorator
