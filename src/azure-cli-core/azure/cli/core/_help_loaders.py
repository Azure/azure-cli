# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from knack.help import HelpParameter as KnackHelpParameter
from azure.cli.core._help import (HelpExample, HelpParameter, CliHelpFile)
from knack.help import HelpAuthoringException


# BaseHelpLoader defining versioned loader interface. Also contains some helper methods.
class BaseHelpLoader(object):
    def __init__(self, help_ctx=None):
        self.help_ctx = help_ctx
    
    def versioned_load(self, help_obj, parser):
        raise NotImplementedError

    @classmethod
    def get_version(cls):
        try:
            cls.VERSION
        except AttributeError:
            raise NotImplementedError

    @staticmethod
    def _get_yaml_help_for_nouns(nouns, cmd_loader_map_ref):
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

        # otherwise likely a group, get the loader
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


class HelpLoaderV0(BaseHelpLoader):
    VERSION = 0

    def versioned_load(self, help_obj, parser):
        super(CliHelpFile, help_obj).load(parser)


class HelpLoaderV1(BaseHelpLoader):
    VERSION = 1

    # load help_obj with data if applicable
    def versioned_load(self, help_obj, parser):
        prog = parser.prog if hasattr(parser, "prog") else parser._prog_prefix
        command_nouns = prog.split()[1:]
        cmd_loader_map_ref = self.help_ctx.cli_ctx.invocation.commands_loader.cmd_to_loader_map

        data = self._get_yaml_help_for_nouns(command_nouns, cmd_loader_map_ref)

        # proceed only if data applies to this help loader
        if not (data and data.get("version", None) == self.VERSION):
            return

        content = data.get("content")
        info_type = None
        info = None
        for elem in content:
            for key, value in elem.items():
                # find the command / group's help text
                if value.get("name") == help_obj.command:
                    info_type = key
                    info = value
                    break

            # found the right entry in content, update help_obj
            if info:
                help_obj.type = info_type
                if "summary" in info:
                    help_obj.short_summary = info["summary"]
                if "description" in info:
                    help_obj.long_summary = info["description"]
                if "links" in info:
                    help_obj.links = info["links"]
                if help_obj.type == "command":
                    self._load_command_data(help_obj, info)
                return

    @classmethod
    def _load_command_data(cls, help_obj, info):
        if "examples" in info:
            help_obj.examples = []
            for ex in info["examples"]:
                if help_obj._should_include_example(ex):
                    help_obj.examples.append(cls._get_example_from_data(ex))

        if "arguments" in info and hasattr(help_obj, "parameters"):
            def _name_is_equal(data, param):
                if data.get('name', None) == param.name:
                    return True
                for name in param.name_source:
                    if data.get("name") == name.lstrip("-"):
                        return True
                return False

            loaded_params = []
            for param in help_obj.parameters:
                loaded_param = next((n for n in info['arguments'] if _name_is_equal(n, param)), None)
                if loaded_param and isinstance(param, KnackHelpParameter):
                    loaded_param["name"] = param.name
                    param.__class__ = HelpParameter  # cast param to CliHelpParameter
                    cls._update_param_from_data(param, loaded_param)
                loaded_params.append(param)

            help_obj.parameters = loaded_params

    @staticmethod
    def _update_param_from_data(ex, data):

        def _raw_value_source_to_string(value_source):
            if "string" in value_source:
                return value_source["string"]
            elif "link" in value_source:
                link_text = ""
                if "url" in value_source["link"]:
                    link_text = "{}".format(value_source["link"]["url"])
                if "command" in value_source["link"]:
                    link_text = "{}".format(value_source["link"]["command"])
                return link_text
            return ""

        if ex.name != data.get('name'):
            raise HelpAuthoringException(u"mismatched name {} vs. {}".format(ex.name, data.get('name')))

        if data.get('summary'):
            ex.short_summary = data.get('summary')

        if data.get('description'):
            ex.long_summary = data.get('description')

        if data.get('value-sources'):
            ex.value_sources = []
            ex.raw_value_sources = data.get('value-sources')
            for value_source in ex.raw_value_sources:
                val_str = _raw_value_source_to_string(value_source)
                if val_str:
                    ex.value_sources.append(val_str)

    @staticmethod
    def _get_example_from_data(_data):
        summary, command, description = _data.get('summary', ''), _data.get('command', ''), _data.get('description', '')
        _data['name'] = summary
        _data['text'] = "{}\n{}".format(description, command) if description else command
        return HelpExample(**_data)
