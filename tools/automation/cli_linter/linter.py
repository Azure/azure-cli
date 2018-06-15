# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import inspect
import argparse
from importlib import import_module
from pkgutil import iter_modules
import yaml
import colorama
from .util import get_command_groups, share_element, exclude_mods


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
            self._command_groups.update(get_command_groups(command_name))

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

    def get_help_entry_parameter_names(self, entry_name):
        return [param_help.get('name', None) for param_help in \
            self._all_yaml_help.get(entry_name).get('parameters', [])]

    def is_valid_parameter_help_name(self, entry_name, param_help_name):
        return param_help_name in [param.name for param in self._loaded_help.get(entry_name).parameters]

    def get_command_help(self, command_name):
        return self._get_loaded_help_description(command_name)

    def get_command_group_help(self, command_group_name):
        return self._get_loaded_help_description(command_group_name)

    def get_parameter_options(self, command_name, parameter_name):
        return self._command_table.get(command_name).arguments.get(parameter_name).type.settings.get('options_list')

    def get_parameter_help(self, command_name, parameter_name):
        options = self.get_parameter_options(command_name, parameter_name)
        parameter_helps = self._loaded_help.get(command_name).parameters
        param_help = next((param for param in parameter_helps if share_element(options, param.name.split())), None)
        # workaround for --ids which is not does not generate doc help (BUG)
        if not param_help:
            return self._command_table.get(command_name).arguments.get(parameter_name).type.settings.get('help')
        return param_help.short_summary or param_help.long_summary

    def _get_loaded_help_description(self, entry):
        return self._loaded_help.get(entry).short_summary or self._loaded_help.get(entry).long_summary


class LinterManager(object):
    def __init__(self, command_table=None, help_file_entries=None, loaded_help=None, exclusions=None,
            rule_inclusions=None):
        self.linter = Linter(command_table=command_table, help_file_entries=help_file_entries, loaded_help=loaded_help)
        self._exclusions = exclusions or {}
        self._rules = {
            'help_file_entries': {},
            'command_groups': {},
            'commands': {},
            'params': {}
        }
        self._ci_exclusions = {}
        self._rule_inclusions = rule_inclusions
        self._loaded_help = loaded_help
        self._command_table = command_table
        self._help_file_entries = help_file_entries
        self._exit_code = 0
        self._ci = False

    def add_rule(self, rule_type, rule_name, rule_callable):
        include_rule = not self._rule_inclusions or rule_name in self._rule_inclusions
        if rule_type in self._rules and include_rule:
            def get_linter():
                if rule_name in self._ci_exclusions and self._ci:
                    mod_exclusions = self._ci_exclusions[rule_name]
                    command_table, help_file_entries = exclude_mods(self._command_table, self._help_file_entries,
                                                                    mod_exclusions)
                    return Linter(command_table=command_table, help_file_entries=help_file_entries,
                                  loaded_help=self._loaded_help)
                return self.linter
            self._rules[rule_type][rule_name] = rule_callable, get_linter

    def mark_rule_failure(self):
        self._exit_code = 1

    @property
    def exclusions(self):
        return self._exclusions

    @property
    def exit_code(self):
        return self._exit_code

    def run(self, run_params=None, run_commands=None, run_command_groups=None, run_help_files_entries=None, ci=False):
        self._ci = ci
        paths = import_module('automation.cli_linter.rules').__path__

        if paths:
            ci_exclusions_path = os.path.join(paths[0], 'ci_exclusions.yml')
            self._ci_exclusions = yaml.load(open(ci_exclusions_path)) or {}

        # find all defined rules and check for name conflicts
        found_rules = set()
        for _, name, _ in iter_modules(paths):
            rule_module = import_module('automation.cli_linter.rules.' + name)
            functions = inspect.getmembers(rule_module, inspect.isfunction)
            for rule_name, add_to_linter_func in functions:
                if hasattr(add_to_linter_func, 'linter_rule'):
                    if rule_name in found_rules:
                        raise Exception('Multiple rules found with the same name: %s' % rule_name)
                    found_rules.add(rule_name)
                    add_to_linter_func(self)

        colorama.init()
        # run all rule-checks
        if run_help_files_entries and self._rules.get('help_file_entries'):
            self._run_rules('help_file_entries')

        if run_command_groups and self._rules.get('command_groups'):
            self._run_rules('command_groups')

        if run_commands and self._rules.get('commands'):
            self._run_rules('commands')

        if run_params and self._rules.get('params'):
            self._run_rules('params')

        if not self.exit_code:
            print(os.linesep + 'No violations found.')
        colorama.deinit()
        return self.exit_code

    def _run_rules(self, rule_group):
        from colorama import Fore
        for rule_name, (rule_func, linter_callable) in self._rules.get(rule_group).items():
            # use new linter if needed
            with LinterScope(self, linter_callable):
                violations = sorted(rule_func()) or []
                if violations:
                    print('- {} FAIL{}: {}'.format(Fore.RED, Fore.RESET, rule_name))
                    for violation_msg in violations:
                        print(violation_msg)
                    print()
                else:
                    print('- {} pass{}: {} '.format(Fore.GREEN, Fore.RESET, rule_name))


class RuleError(Exception):
    """
    Exception thrown by rule violation
    """
    pass


class LinterScope():
    def __init__(self, linter_manager, linter_callable):
        self.linter_manager = linter_manager
        self.linter = linter_callable()
        self.main_linter = linter_manager.linter

    def __enter__(self):
        self.linter_manager.linter = self.linter

    def __exit__(self, exc_type, value, traceback):
        self.linter_manager.linter = self.main_linter
