# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import abc
import os

from azure.cli.core._help import (HelpExample, CliHelpFile)

from knack.util import CLIError
from knack.log import get_logger

import yaml

logger = get_logger(__name__)

try:
    ABC = abc.ABC
except AttributeError:  # Python 2.7, abc exists, but not ABC
    ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})


# BaseHelpLoader defining versioned loader interface. Also contains some helper methods.
class BaseHelpLoader(ABC):
    def __init__(self, help_ctx=None):
        self.help_ctx = help_ctx
        self._entry_data = None
        self._file_content_dict = {}

    def versioned_load(self, help_obj, parser):
        if not self._file_content_dict:
            return
        self._entry_data = None
        # Cycle through versioned_load helpers
        self.load_entry_data(help_obj, parser)
        if self._data_is_applicable():
            self.load_help_body(help_obj)
            self.load_help_parameters(help_obj)
            self.load_help_examples(help_obj)
        self._entry_data = None

    def update_file_contents(self, file_contents):
        self._file_content_dict.update(file_contents)

    @abc.abstractmethod
    def get_noun_help_file_names(self, nouns):
        pass

    @property
    @abc.abstractmethod
    def version(self):
        pass

    def _data_is_applicable(self):
        return self._entry_data and self.version == self._entry_data.get('version')

    @abc.abstractmethod
    def load_entry_data(self, help_obj, parser):
        pass

    @abc.abstractmethod
    def load_help_body(self, help_obj):
        pass

    @abc.abstractmethod
    def load_help_parameters(self, help_obj):
        pass

    @abc.abstractmethod
    def load_help_examples(self, help_obj):
        pass

    # Loader static helper methods

    # Update a help file object from a data dict using the attribute to key mapping
    @staticmethod
    def _update_obj_from_data_dict(obj, data, attr_key_tups):
        for attr, key in attr_key_tups:
            try:
                setattr(obj, attr, data[key] or attr)
            except (AttributeError, KeyError):
                pass

    # update relevant help file object parameters from data.
    @staticmethod
    def _update_help_obj_params(help_obj, data_params, params_equal, attr_key_tups):
        loaded_params = []
        for param_obj in help_obj.parameters:
            loaded_param = next((n for n in data_params if params_equal(param_obj, n)), None)
            if loaded_param:
                BaseHelpLoader._update_obj_from_data_dict(param_obj, loaded_param, attr_key_tups)
            loaded_params.append(param_obj)
        help_obj.parameters = loaded_params


class YamlLoaderMixin:  # pylint:disable=too-few-public-methods
    """A class containing helper methods for Yaml Loaders."""

    # get the list of yaml help file names for the command or group
    @staticmethod
    def _get_yaml_help_files_list(nouns, cmd_loader_map_ref):
        import inspect

        command_nouns = " ".join(nouns)
        # if command in map, get the loader. Path of loader is path of helpfile.
        ldr_or_none = cmd_loader_map_ref.get(command_nouns, [None])[0]
        if ldr_or_none:
            loaders = {ldr_or_none}
        else:
            loaders = set()

        # otherwise likely a group, try to find all command loaders under group as the group help could be defined
        # in either.
        if not loaders:
            for cmd_name, cmd_ldr in cmd_loader_map_ref.items():
                # if first word in loader name is the group, this is a command in the command group
                if cmd_name.startswith(command_nouns + " "):
                    loaders.add(cmd_ldr[0])

        results = []
        if loaders:
            for loader in loaders:
                loader_file_path = inspect.getfile(loader.__class__)
                dir_name = os.path.dirname(loader_file_path)
                files = os.listdir(dir_name)
                for file in files:
                    if file.endswith("help.yaml") or file.endswith("help.yml"):
                        help_file_path = os.path.join(dir_name, file)
                        results.append(help_file_path)
        return results

    @staticmethod
    def _parse_yaml_from_string(text, help_file_path):
        dir_name, base_name = os.path.split(help_file_path)
        pretty_file_path = os.path.join(os.path.basename(dir_name), base_name)

        if not text:
            raise CLIError("No content passed for {}.".format(pretty_file_path))

        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as e:
            raise CLIError("Error parsing {}:\n\n{}".format(pretty_file_path, e))


class HelpLoaderV0(BaseHelpLoader):

    @property
    def version(self):
        return 0

    def versioned_load(self, help_obj, parser):
        super(CliHelpFile, help_obj).load(parser)  # pylint:disable=bad-super-call

    def get_noun_help_file_names(self, nouns):
        pass

    def load_entry_data(self, help_obj, parser):
        pass

    def load_help_body(self, help_obj):
        pass

    def load_help_parameters(self, help_obj):
        pass

    def load_help_examples(self, help_obj):
        pass


class HelpLoaderV1(BaseHelpLoader, YamlLoaderMixin):
    core_attrs_to_keys = [("short_summary", "summary"), ("long_summary", "description")]
    body_attrs_to_keys = core_attrs_to_keys + [("links", "links")]
    param_attrs_to_keys = core_attrs_to_keys + [("value_sources", "value-sources")]

    @property
    def version(self):
        return 1

    def get_noun_help_file_names(self, nouns):
        cmd_loader_map_ref = self.help_ctx.cli_ctx.invocation.commands_loader.cmd_to_loader_map
        return self._get_yaml_help_files_list(nouns, cmd_loader_map_ref)

    def update_file_contents(self, file_contents):
        for file_name in file_contents:
            if file_name not in self._file_content_dict:
                data_dict = {file_name: self._parse_yaml_from_string(file_contents[file_name], file_name)}
                self._file_content_dict.update(data_dict)

    def load_entry_data(self, help_obj, parser):
        prog = parser.prog if hasattr(parser, "prog") else parser._prog_prefix  # pylint: disable=protected-access
        command_nouns = prog.split()[1:]
        cmd_loader_map_ref = self.help_ctx.cli_ctx.invocation.commands_loader.cmd_to_loader_map

        files_list = self._get_yaml_help_files_list(command_nouns, cmd_loader_map_ref)
        data_list = [self._file_content_dict[name] for name in files_list]

        self._entry_data = self._get_entry_data(help_obj.command, data_list)

    def load_help_body(self, help_obj):
        help_obj.long_summary = ""  # similar to knack...
        self._update_obj_from_data_dict(help_obj, self._entry_data, self.body_attrs_to_keys)

    def load_help_parameters(self, help_obj):
        def params_equal(param, param_dict):
            if param_dict['name'].startswith("--"):  # for optionals, help file name must be one of the  long options
                return param_dict['name'] in param.name.split()
            # for positionals, help file must name must match param name shown when -h is run
            return param_dict['name'] == param.name

        if help_obj.type == "command" and hasattr(help_obj, "parameters") and self._entry_data.get("arguments"):
            loaded_params = []
            for param_obj in help_obj.parameters:
                loaded_param = next((n for n in self._entry_data["arguments"] if params_equal(param_obj, n)), None)
                if loaded_param:
                    self._update_obj_from_data_dict(param_obj, loaded_param, self.param_attrs_to_keys)
                loaded_params.append(param_obj)
            help_obj.parameters = loaded_params

    def load_help_examples(self, help_obj):
        if help_obj.type == "command" and self._entry_data.get("examples"):
            help_obj.examples = [HelpExample(**ex) for ex in self._entry_data["examples"] if help_obj._should_include_example(ex)]  # pylint: disable=line-too-long, protected-access

    @staticmethod
    def _get_entry_data(cmd_name, data_list):
        for data in data_list:
            if data and data.get("content"):
                try:
                    entry_data = next(value for elem in data.get("content")
                                      for key, value in elem.items() if value.get("name") == cmd_name)
                    entry_data["version"] = data['version']
                    return entry_data
                except StopIteration:
                    continue
        return None
