# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import json
import inspect
import argparse
from importlib import import_module
from pkgutil import iter_modules


class Linter():
    def __init__(self, command_table=None, help_file_entries=None, loaded_help=None):
        self._command_table = command_table
        self._all_yaml_help = help_file_entries
        self._loaded_help = loaded_help
        self._commands = set(command_table.keys())
        self._command_groups = set()
        self._parameters = {}
        self._help_file_entries = set(help_file_entries.keys())
        self._exit_code = 0
        self._exclusions = None

        self._rules = {
            'help_file_entries': [],
            'command_groups': [],
            'commands': [],
            'params': []
        }

        # get all unsupressed parameters
        for command_name, command in command_table.items():
            self._parameters[command_name] = set()
            for name, param in command.arguments.items():
                if param.type.settings.get('help') != argparse.SUPPRESS:
                    self._parameters[command_name].add(name)

        # populate command groups
        for command_name in self._commands:
            command_args = []
            for arg in command_name.split()[:-1]:
                command_args.append(arg)
                if command_args:
                    self._command_groups.add(' '.join(command_args))

    def get_commands(self):
        return self._commands

    def get_command_groups(self):
        return self._command_groups

    def get_help_file_entries(self):
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

    def get_help_entry_exclusions(self):
        return self._exclusions.get('help_entries')

    def get_command_group_exclusions(self):
        return self._exclusions.get('command_groups')

    def get_command_exclusions(self):
        return self._exclusions.get('commands')

    def get_parameter_exclusions(self, command_name):
        return self._exclusions.get('params').get(command_name, {})

    def add_rule(self, rule_type, rule_callable):
        if rule_type in self._rules:
            self._rules.get(rule_type).append(rule_callable)

    def mark_rule_failure(self):
        self._exit_code = 1

    def run(self, run_params=None, run_commands=None, run_command_groups=None, run_help_files_entries=None):
        paths = import_module('automation.cli_linter.rules').__path__
        exclusion_path = os.path.join(paths[0], 'exclusions.json')
        self._exclusions = json.load(open(exclusion_path))

        # find all defined rules and check for name conflicts
        found_rules = set()
        for _, name, _ in iter_modules(paths):
            rule_module = import_module('automation.cli_linter.rules.' + name)
            functions = inspect.getmembers(rule_module, inspect.isfunction)
            for rule_name, add_to_linter_func in functions:
                if hasattr(add_to_linter_func, 'linter_rule'):
                    if rule_name in found_rules:
                        raise Exception('Multiple rules found with the same name.')
                    found_rules.add(rule_name)
                    add_to_linter_func(self)

        # run all rule-checks
        if run_help_files_entries:
            print('Running Linter on Help File Entries:')
            for callable_rule in self._rules.get('help_file_entries'):
                callable_rule()
                print(os.linesep)

        if run_command_groups:
            print('Running Linter on Command Groups:')
            for callable_rule in self._rules.get('command_groups'):
                callable_rule()
                print(os.linesep)

        if run_commands:
            print('Running Linter on Commands:')
            for callable_rule in self._rules.get('commands'):
                callable_rule()
                print(os.linesep)

        if run_params:
            print('Running Linter on Parameters:')
            for callable_rule in self._rules.get('params'):
                callable_rule()
                print(os.linesep)

        return self._exit_code

    def _get_loaded_help_description(self, entry):
        return self._loaded_help.get(entry).short_summary or self._loaded_help.get(entry).long_summary

def _share_element(first_iter, second_iter):
    return any(element in first_iter for element in second_iter)
