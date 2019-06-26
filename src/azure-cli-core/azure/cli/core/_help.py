# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

from knack.help import (HelpExample as KnackHelpExample, HelpFile as KnackHelpFile, CommandHelpFile as KnackCommandHelpFile,
                        CLIHelp, ArgumentGroupRegistry as KnackArgumentGroupRegistry, HelpAuthoringException)

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


# PrintMixin class to decouple printing functionality from AZCLIHelp class.
class CLIPrintMixin(CLIHelp):
    def _print_detailed_help(self, cli_name, help_file):
        CLIPrintMixin._print_extensions_msg(help_file)
        super(CLIPrintMixin, self)._print_detailed_help(cli_name, help_file)

    @staticmethod
    def _print_extensions_msg(help_file):
        if help_file.type != 'command':
            return
        if isinstance(help_file.command_source, ExtensionCommandSource):
            logger.warning(help_file.command_source.get_command_warn_msg())
            if help_file.command_source.preview:
                logger.warning(help_file.command_source.get_preview_warn_msg())


class AzCliHelp(CLIPrintMixin, CLIHelp):

    def __init__(self, cli_ctx):
        super(AzCliHelp, self).__init__(cli_ctx,
                                        privacy_statement=PRIVACY_STATEMENT,
                                        welcome_message=WELCOME_MESSAGE,
                                        command_help_cls=CliCommandHelpFile,
                                        help_cls=CliHelpFile)
        from knack.help import HelpObject

        # TODO: This workaround is used to avoid a bizarre bug in Python 2.7. It
        # essentially reassigns Knack's HelpObject._normalize_text implementation
        # with an identical implemenation in Az. For whatever reason, this fixes
        # the bug in Python 2.7.
        @staticmethod
        def new_normalize_text(s):
            if not s or len(s) < 2:
                return s or ''
            s = s.strip()
            initial_upper = s[0].upper() + s[1:]
            trailing_period = '' if s[-1] in '.!?' else '.'
            return initial_upper + trailing_period

        HelpObject._normalize_text = new_normalize_text  # pylint: disable=protected-access


class CliHelpFile(KnackHelpFile):

    def _should_include_example(self, ex):
        supported_profiles = ex.get('supported-profiles')
        unsupported_profiles = ex.get('unsupported-profiles')

        if all((supported_profiles, unsupported_profiles)):
            raise HelpAuthoringException("An example cannot have both supported-profiles and unsupported-profiles.")

        if supported_profiles:
            supported_profiles = [profile.strip() for profile in supported_profiles.split(',')]
            return self.help_ctx.cli_ctx.cloud.profile in supported_profiles

        if unsupported_profiles:
            unsupported_profiles = [profile.strip() for profile in unsupported_profiles.split(',')]
            return self.help_ctx.cli_ctx.cloud.profile not in unsupported_profiles

        return True

    # Needs to override base implementation to exclude unsupported examples.
    def _load_from_data(self, data):
        super(CliHelpFile, self)._load_from_data(data)
        self.examples = []  # clear examples set by knack

        if 'examples' in data:
            self.examples = []
            for d in data['examples']:
                if self._should_include_example(d):
                    self.examples.append(HelpExample(d))


class CliCommandHelpFile(KnackCommandHelpFile, CliHelpFile):

    def __init__(self, help_ctx, delimiters, parser):
        self.command_source = getattr(parser, 'command_source', None)
        super(CliCommandHelpFile, self).__init__(help_ctx, delimiters, parser)


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


# override to add support for supported and unsupported profiles
class HelpExample(KnackHelpExample):  # pylint: disable=too-few-public-methods

    def __init__(self, _data):
        # Old attributes
        super(HelpExample, self).__init__(_data)
        self.supported_profiles = _data.get('supported-profiles', None)
        self.unsupported_profiles = _data.get('unsupported-profiles', None)
