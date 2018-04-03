# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import inspect
import argparse
from importlib import import_module
from pkgutil import iter_modules


class Linter(object):
    def __init__(self, command_table=None, help_file_entries=None, loaded_help=None):
        self._command_table = command_table
        self._all_yaml_help = help_file_entries
        self._loaded_help = loaded_help
        self._commands = set(command_table.keys())
        self._command_groups = set()
        self._parameters = {}
        self._help_file_entries = set(help_file_entries.keys())

        # get all unsupressed parameters
        for command_name, command in command_table.items():
            self._parameters[command_name] = set()
            for name, param in command.arguments.items():
                if param.type.settings.get('help') != argparse.SUPPRESS:
                    self._parameters[command_name].add(name)

        # populate command groups
        for command_name in self._commands:
            self._command_groups.update(_get_command_groups(command_name))

    @property
    def commands(self):
        return self._commands

    @property
    def command_groups(self):
        return self._command_groups

    @property
    def help_file_entries(self):
        return self._help_file_entries

    def get_command_parameters(self, command_name):
        return self._parameters.get(command_name)

    def get_help_entry_type(self, entry_name):
        return self._all_yaml_help.get(entry_name).get('type')

    def get_command_help(self, command_name):
        return self._get_loaded_help_description(command_name)

    def get_command_group_help(self, command_group_name):
        return self._get_loaded_help_description(command_group_name)

    def get_parameter_help(self, command_name, parameter_name):
        options = self._command_table.get(command_name).arguments.get(parameter_name).type.settings.get('options_list')
        parameter_helps = self._loaded_help.get(command_name).parameters
        param_help = next((param for param in parameter_helps if _share_element(options, param.name.split())), None)
        # workaround for --ids which is not does not generate doc help (BUG)
        if not param_help:
            return self._command_table.get(command_name).arguments.get(parameter_name).type.settings.get('help')
        return param_help.short_summary or param_help.long_summary


    def _get_loaded_help_description(self, entry):
        return self._loaded_help.get(entry).short_summary or self._loaded_help.get(entry).long_summary


class LinterManager(object):
    def __init__(self, command_table=None, help_file_entries=None, loaded_help=None, exclusions={}):
        self.linter = Linter(command_table=command_table, help_file_entries=help_file_entries, loaded_help=loaded_help)
        self._exclusions = exclusions
        self._rules = {
            'help_file_entries': [],
            'command_groups': [],
            'commands': [],
            'params': []
        }
        self._exit_code = 0

    def add_rule(self, rule_type, rule_callable):
        if rule_type in self._rules:
            self._rules.get(rule_type).append(rule_callable)

    def mark_rule_failure(self):
        self._exit_code = 1

    @property
    def exclusions(self):
        return self._exclusions

    @property
    def exit_code(self):
        return self._exit_code

    def run(self, run_params=None, run_commands=None, run_command_groups=None, run_help_files_entries=None, ci=False):
        paths = import_module('automation.cli_linter.rules').__path__

        # find all defined rules and check for name conflicts
        found_rules = set()
        for _, name, _ in iter_modules(paths):
            rule_module = import_module('automation.cli_linter.rules.' + name)
            functions = inspect.getmembers(rule_module, inspect.isfunction)
            for rule_name, add_to_linter_func in functions:
                if hasattr(add_to_linter_func, 'linter_rule'):
                    if rule_name in found_rules:
                        raise Exception('Multiple rules found with the same name: %s' % rule_name)
                    if ci and hasattr(add_to_linter_func, 'exclude_from_ci'):
                        continue
                    found_rules.add(rule_name)
                    add_to_linter_func(self)

        # run all rule-checks
        if run_help_files_entries and self._rules.get('help_file_entries'):
            print(os.linesep + 'Running Linter on Help File Entries:')
            self._run_rules('help_file_entries')

        if run_command_groups and self._rules.get('command_groups'):
            print(os.linesep + 'Running Linter on Command Groups:')
            self._run_rules('command_groups')

        if run_commands and self._rules.get('commands'):
            print(os.linesep + 'Running Linter on Commands:')
            self._run_rules('commands')

        if run_params and self._rules.get('params'):
            print(os.linesep + 'Running Linter on Parameters:')
            self._run_rules('params')

        return self.exit_code

    def _run_rules(self, rule_group):
        for callable_rule in self._rules.get(rule_group):
            for violation_msg in sorted(callable_rule()):
                print(violation_msg)
            print()


class RuleError(Exception):
    """
    Exception thrown by rule violation
    """
    pass


def _share_element(first_iter, second_iter):
    return any(element in first_iter for element in second_iter)

def _get_command_groups(command_name):
    command_args = []
    for arg in command_name.split()[:-1]:
        command_args.append(arg)
        if command_args:
            yield ' '.join(command_args)
