# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

from knack.help import (HelpExample,
                        HelpFile as KnackHelpFile,
                        CommandHelpFile as KnackCommandHelpFile,
                        GroupHelpFile as KnackGroupHelpFile,
                        CLIHelp,
                        HelpParameter,
                        ArgumentGroupRegistry as KnackArgumentGroupRegistry)
from knack.log import get_logger
from knack.util import CLIError

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
        super(AzCliHelp, self).__init__(cli_ctx,
                                        privacy_statement=PRIVACY_STATEMENT,
                                        welcome_message=WELCOME_MESSAGE,
                                        command_help_cls=CliCommandHelpFile,
                                        group_help_cls=CliGroupHelpFile,
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

    @staticmethod
    def _print_extensions_msg(help_file):
        if help_file.type != 'command':
            return
        if isinstance(help_file.command_source, ExtensionCommandSource):
            logger.warning(help_file.command_source.get_command_warn_msg())
            if help_file.command_source.preview:
                logger.warning(help_file.command_source.get_preview_warn_msg())

    def _print_detailed_help(self, cli_name, help_file):
        AzCliHelp._print_extensions_msg(help_file)
        super(AzCliHelp, self)._print_detailed_help(cli_name, help_file)


class CliHelpFile(KnackHelpFile):

    def __init__(self, help_ctx, delimiters):
        # Each help file (for a command or group) has a version denoting the source of its data.
        self.yaml_help_version = 0
        super(CliHelpFile, self).__init__(help_ctx, delimiters)

    def _should_include_example(self, ex):
        min_profile = ex.get('min_profile')
        max_profile = ex.get('max_profile')
        if min_profile or max_profile:
            from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE
            # yaml will load this as a datetime if it's a date, we need a string.
            min_profile = str(min_profile) if min_profile else None
            max_profile = str(max_profile) if max_profile else None
            return supported_api_version(self.help_ctx.cli_ctx, resource_type=PROFILE_TYPE,
                                         min_api=min_profile, max_api=max_profile)
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

    def load(self, options):
        # if the parser's command has an associated yaml help file, load data from it.
        prog = options.prog if hasattr(options, "prog") else options._prog_prefix
        command_nouns = prog.split()[1:]
        cmd_loader_map_ref = self.help_ctx.cli_ctx.invocation.commands_loader.cmd_to_loader_map

        yaml_help = get_yaml_help_for_nouns(command_nouns, cmd_loader_map_ref)
        if yaml_help and "version" in yaml_help:
            self.yaml_help_version = yaml_help["version"]

        if self.yaml_help_version == 1:
            from azure.cli.core._help_util import update_help_file
            update_help_file(self, yaml_help, options)
            return

        # Previous behavior. "version 0"
        else:
            super(CliHelpFile, self).load(options)


class CliGroupHelpFile(KnackGroupHelpFile, CliHelpFile):
    def __init__(self, help_ctx, delimiters, parser):
        super(CliGroupHelpFile, self).__init__(help_ctx, delimiters, parser)

    def load(self, options):
        # forces class to use this load method even if KnackGroupHelpFile overrides CliHelpFile's method.
        CliHelpFile.load(self, options)


class CliCommandHelpFile(KnackCommandHelpFile, CliHelpFile):

    def __init__(self, help_ctx, delimiters, parser):
        self.command_source = getattr(parser, 'command_source', None)
        self.parameters = []

        for action in [a for a in parser._actions if a.help != argparse.SUPPRESS]:  # pylint: disable=protected-access
            if action.option_strings:
                self._add_parameter_help(action)
            else:
                # use metavar for positional parameters
                param_kwargs = {
                    'name_source': [action.metavar or action.dest],
                    'deprecate_info': getattr(action, 'deprecate_info', None),
                    'description': action.help,
                    'choices': action.choices,
                    'required': False,
                    'default': None,
                    'group_name': 'Positional'
                }
                self.parameters.append(HelpParameter(**param_kwargs))

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

    def load(self, options):
        # forces class to use this load method even if KnackGroupHelpFile overrides CliHelpFile's method.
        CliHelpFile.load(self, options)

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


def get_yaml_help_for_nouns(nouns, cmd_loader_map_ref):
    import inspect
    import os

    def _parse_yaml_from_string(text, help_file_path):
        import yaml

        dir_name, base_name = os.path.split(help_file_path)

        pretty_file_path = os.path.join(os.path.basename(dir_name), base_name)

        try:
            data = yaml.load(text)
            if not data:
                raise CLIError("Error: Help file {} is empty".format(pretty_file_path))
            return data
        except yaml.YAMLError as e:
            raise CLIError("Error parsing {}:\n\n{}".format(pretty_file_path, e))

    command_nouns = " ".join(nouns)
    # if command in map, get the loader. Path of loader is path of helpfile.
    loader = cmd_loader_map_ref.get(command_nouns, [None])[0]

    if not loader:
        for k, v in cmd_loader_map_ref.items():
            # if loader name starts with noun / group, this is a command in the command group
            if k.startswith(command_nouns):
                loader = v[0]
                break

    if loader:
        loader_file_path = inspect.getfile(loader.__class__)
        dir_name = os.path.dirname(loader_file_path)
        files = os.listdir(dir_name)
        for file in files:
            if file.endswith(".yaml") or file.endswith(".yml"):
                help_file_path = os.path.join(dir_name, file)
                with open(help_file_path, "r") as f:
                    text = f.read()
                    return _parse_yaml_from_string(text, help_file_path)
    return None