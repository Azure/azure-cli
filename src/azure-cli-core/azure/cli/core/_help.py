# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

from knack.help import (HelpExample, HelpFile as KnackHelpFile, CommandHelpFile as KnackCommandHelpFile,
                        GroupHelpFile as KnackGroupHelpFile, CLIHelp, HelpParameter,
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

    @staticmethod
    def update_parser_with_help_file(nouns, cmd_loader_map, parser, is_group):
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
        loader = None
        if is_group:
            for k, v in cmd_loader_map.items():
                if k.startswith(command_nouns):
                    loader = v[0]
                    break
        else:
            loader = cmd_loader_map.get(command_nouns, [None])[0]

        if loader:
            loader_file_path = inspect.getfile(loader.__class__)
            dir_name = os.path.dirname(loader_file_path)
            files = os.listdir(dir_name)
            for file in files:
                if file.endswith(".yaml") or file.endswith(".yml"):
                    help_file_path = os.path.join(dir_name, file)
                    with open(help_file_path, "r") as f:
                        text = f.read()
                        data = _parse_yaml_from_string(text, help_file_path)
                        parser.help_file_data = data
                        return

    def show_help(self, cli_name, nouns, parser, is_group):
        cmd_loader_map_ref = self.cli_ctx.invocation.commands_loader.cmd_to_loader_map
        # attempt to add the help.yaml file data to the parser
        self.update_parser_with_help_file(nouns, cmd_loader_map_ref, parser, is_group)
        super(AzCliHelp, self).show_help(cli_name, nouns, parser, is_group)


class CliHelpFile(KnackHelpFile):

    def load(self, options):
        # if we successfully transformed the help.yaml data, call appropriate _load_from_data method.
        # This is either CliHelpFile._load_from_data() or CliCommandHelpFile._load_from_data() which ultimately
        # calls CliHelpFile._load_from_data()
        if hasattr(options, "help_file_data"):
            data = self._load_from_parsed_yaml(options.help_file_data)
            if "content" not in data:
                self._load_from_data(data)
                return

        # if unable to transfrom data from parsed yaml, call superclass' (regular) load method
        super(CliHelpFile, self).load(options)

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

    # Needs to override base implementation
    def _load_from_data(self, data):
        super(CliHelpFile, self)._load_from_data(data)
        self.examples = []  # clear examples set by knack
        if 'examples' in data:
            self.examples = []
            for d in data['examples']:
                if self._should_include_example(d):
                    self.examples.append(HelpExample(d))

    # get data object from parsed yaml
    def _load_from_parsed_yaml(self, data):
        content = data.get("content")
        info_type = None
        info = None
        new_data = {}

        for elem in content:
            for key, value in elem.items():
                # find the command / group's help text
                if value.get("name") and value.get("name") == self.command:
                    info_type = key
                    info = value
                    break
            if info:
                break

        # if a new command not found return old data object
        if not info:
            return data

        new_data["type"] = info_type

        if "summary" in info:
            new_data["short-summary"] = info["summary"]

        if "description" in info:
            new_data["long-summary"] = info["description"]

        if "examples" in info:
            new_data["detailed_examples"] = info["examples"]
            reg_examples = []
            for item in new_data["detailed_examples"]:
                ex = {}
                ex["name"] = item.get("summary", "")
                ex["text"] = item.get("description", "")
                ex["text"] = "{}\n{}".format(ex["text"], item.get("command", "")) if ex["text"] else item.get("command", "")
                ex["min_profile"] = item.get('min_profile')
                ex["max_profile"] = item.get('max_profile')
                reg_examples.append(ex)
            new_data["examples"] = reg_examples

        if "links" in info:
            text = self._get_links_as_text(info["links"])
            new_data["links"] = info["links"]
            new_data["long-summary"] = "{}\n{}".format(new_data["long-summary"], text) \
                if new_data.get("long-summary") else text

        if "arguments" in info:
            new_data["parameters"] = []
            for arg_info in info["arguments"]:
                new_data["parameters"].append(self._get_parameter_info(arg_info))

        return new_data

    @staticmethod
    def _get_links_as_text(links):
        text = []
        for link in links:
            if "url" in link:
                text.append(link["url"])
        msg = "For more information, visit:"
        links = ", ".join(text)
        return "{} {}".format(msg, links) if links else ""

    @staticmethod
    def _get_parameter_info(arg_info):
        params = {}

        # only update if new information
        if "name" in arg_info:
            params["name"] = arg_info["name"]

        if "summary" in arg_info:
            params["short-summary"] = arg_info["summary"]

        if "description" in arg_info:
            params["long-summary"] = arg_info["description"]

        if "value-source" in arg_info:
            value_source = []
            for item in arg_info["value-source"]:
                if "string" in item:
                    value_source.append(item["string"])
                elif "link" in item:
                    link_text = ""
                    if "url" in item["link"]:
                        link_text = "url: {} ".format(item["link"]["url"])
                    if "command" in item["link"]:
                        link_text = "command: {} ".format(item["link"]["command"])
                    value_source.append(link_text.strip())
            params["populator-commands"] = value_source

        return params


class CliGroupHelpFile(KnackGroupHelpFile, CliHelpFile):

    def __init__(self, help_ctx, delimiters, parser):

        # try to update internal parsers' help_file_data
        try:
            if parser.choices and parser.help_file_data:
                for options in parser.choices.values():
                    options.help_file_data = parser.help_file_data
        except AttributeError:
            pass

        super(CliGroupHelpFile, self).__init__(help_ctx, delimiters, parser)


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

        def _params_equal(data, param):
            for name in param.name_source:
                if data.get("name") == name.lstrip("-"):
                    return True
            return False

        # load help object from data. Will call CliHelpFile._load_from_data() or KnackCommandHelpFile._load_from_data()
        # based on data contents / caller of this method.
        super(CliCommandHelpFile, self)._load_from_data(data)

        if isinstance(data, str) or not self.parameters or not data.get('parameters'):
            return

        loaded_params = []
        loaded_param = {}
        for param in self.parameters:
            loaded_param = next((n for n in data['parameters'] if _params_equal(n, param)), None)
            if loaded_param:
                loaded_param["name"] = param.name
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
