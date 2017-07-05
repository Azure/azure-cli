# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import sys

from knack.help import \
    (HelpExample, CommandHelpFile, GroupHelpFile, HelpFile as KnackHelpFile, CLIHelp,
     ArgumentGroupRegistry as KnackArgumentGroupRegistry, print_description_list, _print_indent,
     print_detailed_help)


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


WELCOME_MESSAGE = """
    /\\
   /  \\    _____   _ _ __ ___
  / /\ \\  |_  / | | | \'__/ _ \\
 / ____ \\  / /| |_| | | |  __/
/_/    \_\\/___|\__,_|_|  \___|

Welcome to the cool new Azure CLI!

Here are the base commands:
"""

class AzCliHelp(CLIHelp):

    def __init__(self, ctx):
        self.ctx = ctx
        super(AzCliHelp, self).__init__(ctx, PRIVACY_STATEMENT, WELCOME_MESSAGE)


class ArgumentGroupRegistry(KnackArgumentGroupRegistry):  # pylint: disable=too-few-public-methods

    def __init__(self, group_list):

        super(ArgumentGroupRegistry, self).__init__()
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


class HelpFile(KnackHelpFile):  # pylint: disable=too-few-public-methods,too-many-instance-attributes

    @staticmethod
    def _should_include_example(ex):
        min_profile = ex.get('min_profile')
        max_profile = ex.get('max_profile')
        if min_profile or max_profile:
            from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE
            # yaml will load this as a datetime if it's a date, we need a string.
            min_profile = str(min_profile) if min_profile else None
            max_profile = str(max_profile) if max_profile else None
            return supported_api_version(PROFILE_TYPE,
                                         min_api=min_profile,
                                         max_api=max_profile)
        return True

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
                if HelpFile._should_include_example(d):
                    self.examples.append(HelpExample(d))
