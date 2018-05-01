# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

from knack.help import (HelpExample,
                        HelpFile as KnackHelpFile,
                        CLIHelp,
                        HelpParameter,
                        ArgumentGroupRegistry as KnackArgumentGroupRegistry)
from knack.log import get_logger

from azure.cli.core.commands import ExtensionCommandSource

logger = get_logger(__name__)

PRIVACY_STATEMENT = """
Welcome to Azure CLI!
---------------------
Use `az -h` to see available commands or go to https://aka.ms/cli.

Telemetry
---------
The Azure CLI collects usage data in order to improve your experience.
The data is anonymous and does not include commandline argument values.
The data is collected by Microsoft.

You can change your telemetry settings with `az configure`.
"""

WELCOME_MESSAGE = r"""
     /\
    /  \    _____   _ _  ___ _
   / /\ \  |_  / | | | \'__/ _\
  / ____ \  / /| |_| | | |  __/
 /_/    \_\/___|\__,_|_|  \___|


Welcome to the cool new Azure CLI!

Use `az --version` to display the current version.
Here are the base commands:
"""


class AzCliHelp(CLIHelp):

    def __init__(self, cli_ctx):
        self.cli_ctx = cli_ctx
        super(AzCliHelp, self).__init__(cli_ctx, PRIVACY_STATEMENT, WELCOME_MESSAGE)

    @staticmethod
    def _print_extensions_msg(help_file):
        if help_file.type != 'command':
            return
        if help_file.command_source and isinstance(help_file.command_source, ExtensionCommandSource):
            logger.warning(help_file.command_source.get_command_warn_msg())
            if help_file.command_source.preview:
                logger.warning(help_file.command_source.get_preview_warn_msg())

    @classmethod
    def print_detailed_help(cls, cli_name, help_file):
        cls._print_extensions_msg(help_file)
        cls._print_detailed_help(cli_name, help_file)

    @classmethod
    def show_help(cls, cli_name, nouns, parser, is_group):
        from knack.help import GroupHelpFile
        delimiters = ' '.join(nouns)
        help_file = CliCommandHelpFile(delimiters, parser) if not is_group else GroupHelpFile(delimiters, parser)
        help_file.load(parser)
        if not nouns:
            help_file.command = ''
        cls.print_detailed_help(cli_name, help_file)


class CliHelpFile(KnackHelpFile):

    def __init__(self, cli_ctx, delimiters):
        super(CliHelpFile, self).__init__(delimiters)
        self.cli_ctx = cli_ctx

    def _should_include_example(self, ex):
        min_profile = ex.get('min_profile')
        max_profile = ex.get('max_profile')
        if min_profile or max_profile:
            from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE
            # yaml will load this as a datetime if it's a date, we need a string.
            min_profile = str(min_profile) if min_profile else None
            max_profile = str(max_profile) if max_profile else None
            return supported_api_version(self.cli_ctx, resource_type=PROFILE_TYPE,
                                         min_api=min_profile, max_api=max_profile)
        return True

    # Needs to override base implementation
    def _load_from_data(self, data):
        if not data:
            return

        if isinstance(data, str):
            self.long_summary = data
            return

        if 'type' in data:
            self.type = data['type']

        if 'short-summary' in data:
            self.short_summary = data['short-summary']

        self.long_summary = data.get('long-summary')

        if 'examples' in data:
            self.examples = []
            for d in data['examples']:
                if self._should_include_example(d):
                    self.examples.append(HelpExample(d))


class CliCommandHelpFile(CliHelpFile):

    def __init__(self, delimiters, parser):
        super(CliCommandHelpFile, self).__init__(parser.cli_ctx, delimiters)
        import argparse
        self.type = 'command'
        self.command_source = getattr(parser, 'command_source', None)

        self.parameters = []

        for action in [a for a in parser._actions if a.help != argparse.SUPPRESS]:  # pylint: disable=protected-access
            if action.option_strings:
                self.parameters.append(HelpParameter(' '.join(sorted(action.option_strings)),
                                                     action.help,
                                                     required=action.required,
                                                     choices=action.choices,
                                                     default=action.default,
                                                     group_name=action.container.description))
            else:
                self.parameters.append(HelpParameter(action.metavar,
                                                     action.help,
                                                     required=False,
                                                     choices=action.choices,
                                                     default=None,
                                                     group_name='Positional Arguments'))

        help_param = next(p for p in self.parameters if p.name == '--help -h')
        help_param.group_name = 'Global Arguments'

    def _load_from_data(self, data):
        super(CliCommandHelpFile, self)._load_from_data(data)

        if isinstance(data, str) or not self.parameters or not data.get('parameters'):
            return

        loaded_params = []
        loaded_param = {}
        for param in self.parameters:
            loaded_param = next((n for n in data['parameters'] if n['name'] == param.name), None)
            if loaded_param:
                param.update_from_data(loaded_param)
            loaded_params.append(param)

        self.parameters = loaded_params


class ArgumentGroupRegistry(KnackArgumentGroupRegistry):  # pylint: disable=too-few-public-methods

    def __init__(self, group_list):

        super(ArgumentGroupRegistry, self).__init__(group_list)
        self.priorities = {
            None: 0,
            'Resource Id Arguments': 1,
            'Generic Update Arguments': 998,
            'Global Arguments': 1000,
        }
        priority = 2
        # any groups not already in the static dictionary should be prioritized alphabetically
        other_groups = [g for g in sorted(list(set(group_list))) if g not in self.priorities]
        for group in other_groups:
            self.priorities[group] = priority
            priority += 1
