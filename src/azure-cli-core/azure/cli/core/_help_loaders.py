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
        self._data = None
    
    def versioned_load(self, help_obj, parser):
        self._load_raw_data(help_obj, parser)
        if self._data_is_applicable():
            self._load_help_body(help_obj)
            self._load_help_parameters(help_obj)
            self._load_help_examples(help_obj)

    @classmethod
    def get_version(cls):
        try:
            cls.VERSION
        except AttributeError:
            raise NotImplementedError

    def _data_is_applicable(self):
        return self._data and self.get_version() == self._data.get('version')

    def _load_raw_data(self, help_obj, parser):
        raise NotImplementedError

    def _load_help_body(self, help_obj):
        raise NotImplementedError

    def _load_help_parameters(self, help_obj):
        raise NotImplementedError

    def _load_help_examples(self, help_obj):
        raise NotImplementedError

    # Loader static helper methods

    # Update a help file object from a data dict using the attribute to key mapping
    @staticmethod
    def _update_help_obj(help_obj, data, attr_key_tups):
        for attr, key in attr_key_tups:
            try:
                setattr(help_obj, attr, data[key])
            except (AttributeError, KeyError):
                pass

    # update relevant help file object parameters from data.
    @staticmethod
    def _update_help_obj_params(help_obj, data_params, params_equal):
        loaded_params = []
        loaded_param = {}
        for param in help_obj.parameters:
            loaded_param = next((n for n in data_params if params_equal(param, n)), None)
            if loaded_param:
                param.update_from_data(loaded_param)
            loaded_params.append(param)
        help_obj.parameters = loaded_params

    # get the yaml help
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

    def _load_raw_data(self, help_obj, parser):
        prog = parser.prog if hasattr(parser, "prog") else parser._prog_prefix
        command_nouns = prog.split()[1:]
        cmd_loader_map_ref = self.help_ctx.cli_ctx.invocation.commands_loader.cmd_to_loader_map
        self._data = BaseHelpLoader._get_yaml_help_for_nouns(command_nouns, cmd_loader_map_ref)
        self._command_data = self._get_command_data(help_obj.command, self._data)

    def _load_help_body(self, help_obj):
        attr_key_tups = [("short_summary", "summary"), ("long_summary", "description"), ("links", "links")]
        if self._command_data:
            self._update_help_obj(help_obj, self._command_data, attr_key_tups)

    def _load_help_parameters(self, help_obj):
        def params_equal(param, param_dict):
            return param == param_dict['name']
        if self._command_data:
            self._update_help_obj_params(help_obj, self._command_data.get("arguments", []), params_equal)


    @staticmethod
    def _get_command_data(cmd_name, data):
        if data and data.get("content"):
            try:
                return next(value for elem in data.get("content") for key, value in elem.items() if value.get("name") == cmd_name)
            except StopIteration:
                pass
        return None

    @classmethod
    def _load_command_data(cls, help_obj, info):
        if "examples" in info:
            help_obj.examples = []
            for ex in info["examples"]:
                if help_obj._should_include_example(ex):
                    help_obj.examples.append(cls._get_example_from_data(ex))

    @staticmethod
    def _get_example_from_data(_data):
        summary, command, description = _data.get('summary', ''), _data.get('command', ''), _data.get('description', '')
        _data['name'] = summary
        _data['text'] = "{}\n{}".format(description, command) if description else command
        return HelpExample(**_data)
